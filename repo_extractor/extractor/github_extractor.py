"""Exposes functionality to mine GitHub repositories."""

# import datetime
import sys
import time
import github
from repo_extractor import conf, schema
from repo_extractor.extractor import _sessions
from repo_extractor.utils import dict_utils, file_io_utils

# ANSI escape sequence for clearing a row in the console:
# credit: https://stackoverflow.com/a/64245513
CLR = "\x1b[K"
TAB = " " * 4


class Extractor:
    """The Extractor class contains GitHub REST API functionality."""

    # ----------------------------------------------------------------------
    # Initialization tools
    # ----------------------------------------------------------------------
    def __init__(self, cfg_obj: conf.Cfg) -> None:
        """
        Extractor object initialization.

        This object is our top-level actor and must be used by the user
        to extract data, such as in a driver program.

        Args:
            cfg_obj (conf.Cfg): configuration object.

        Attributes:
            cfg (conf.Cfg): configuration object.
            gh_sesh (github.Github): GitHub connection object.
            issues_paged_list (github.PaginatedList of github.Issue): the
                paginated list containing all issues of the chosen type
                for the repository.
        """
        self.cfg = cfg_obj

        # create output path so that it is already ready for work. The
        # JSON writing functionality will check if it exists later and
        # create it again if something happened to it during execution,
        # attempting to circumvent TOCTOU errors that will crash
        # execution. Because this program can be very long-running,
        # multiple checks are smart because the filesystem can change.
        file_io_utils.mk_json_outpath(self.get_cfg_val("output_path"))

        # initialize authenticated GitHub session
        self.gh_sesh = _sessions.GithubSession(self.get_cfg_val("auth_path"))

        self.repo_metadata = self.__get_repo_metadata()

        self.cfg.set_cfg_val("range", self.__get_sanitized_cfg_range())

    def __get_repo_obj(self):
        """
        TODO.

        Returns:
            github.Repository.Repository: repo obj for current extraction op
        """
        job_repo = self.get_cfg_val("repo")

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Cannot access "{job_repo}"!')
                print(f"{TAB}It either does not exist or is private!")
                sys.exit(1)

            else:
                return repo_obj

    def __get_issues_paged_list(self, repo_obj, state: str):
        """
        Retrieve and store a paginated list from GitHub.

        Raises:
            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, sleep the program until
                calls can be made again and continue attempt to
                collect desired paginated list.

            github.UnknownObjectException: this exception is
                thrown at least when a repository is not
                accessible. This is can occur because the repo
                is private or does not exist, but may occur
                for other, unforeseen reasons.

        Returns:
            github.PaginatedList of github.Issue.
        """
        while True:
            try:
                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state=state
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            else:
                return issues_paged_list

    def __get_repo_metadata(self) -> dict:

        repo = self.__get_repo_obj()

        state: str = self.cfg.get_repo_data_cfg_val("state")

        paged_list = self.__get_issues_paged_list(repo, state)

        # get index of last page in paginated list
        last_page_index: int = (
            paged_list.totalCount - 1
        ) // self.gh_sesh.get_pg_len()

        return {"paged_list": paged_list, "last_page_index": last_page_index}

    def __get_sanitized_cfg_range(self):

        last_page_index = self.repo_metadata["last_page_index"]
        paged_list = self.repo_metadata["paged_list"]
        range_list: list = self.cfg.get_repo_data_cfg_val("range")

        # get the highest item num in the paginated list of items,
        # e.g. very last PR num
        last_page = paged_list.get_page(last_page_index)
        last_item = last_page[-1]
        highest_num = last_item.number

        # get sanitized range. This will correct any vals given in
        # the range cfg so that they are within the values that are
        # in the paged list. We are protected from too low of values
        # by the Cerberus config schema, so this process only looks
        # at values that are too high.
        return [
            min(val, highest_num) for val in (range_list[0], range_list[-1])
        ]

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    def get_cfg_val(self, key: str):
        """
        Wrap cfg.get_cfg_val for brevity.

        Args:
            key (str): key of desired value from configuration dict to get.

        Returns:
            value from configuration dict.

        Todo:
            give the output a comprehensive type and adjust other
            methods accordingly.
        """
        return self.cfg.get_cfg_val(key)

    @staticmethod
    def __get_item_data(
        category_dict: dict, field_type: str, cur_item
    ) -> dict:
        """
        Getter engine used to aggregate desired data from a given API item.

        For each field in the list provided by the user in
        configuration, e.g. "issue_fields", get the associated
        piece of data and store it in a dict where
        {field name: field data}, e.g. {"issue number": 20}.

        Args:
            user_cfg (conf.Cfg): Cfg object containing user-provided
                configuration
            item_type (str): name of item type to retrieve, e.g.
                "pr" or "issue"
            cur_item (github.Issue/PullRequest/Commit): the current
                API item to get data about, e.g. current PR

        Returns:
            dict: dictionary of API data values for param item
        """
        field_list = category_dict[f"{field_type}_fields"]

        if len(field_list) > 0:
            cmd_tbl = schema.cmd_tbl_dict[field_type]

            # when called, this will resolve to various function calls, e.g.
            # "body": cmd_tbl["body"](cur_PR)
            return {field: cmd_tbl[field](cur_item) for field in field_list}

        return {}

    def __sleep_extractor(self) -> None:
        """Sleep the program until we can make calls again."""
        cntdown_time = self.gh_sesh.get_remaining_ratelimit_time()

        while cntdown_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(cntdown_time, 60)

            # format the time string before printing
            cntdown_str = f"{minutes:02d}:{seconds:02d}"

            print(
                f"{CLR}{TAB * 2}Time until limit reset: {cntdown_str}",
                end="\r",
            )

            # sleep for a while
            time.sleep(1)
            cntdown_time -= 1

        print(f"{CLR}{TAB * 2}Starting data collection...", end="\r")

    def __update_output_json_for_sleep(
        self, data_dict: dict, out_file: str
    ) -> dict:
        """
        Write collected data to output and sleep the program.

        When rate limited, we can update the JSON dict in the output
        file with the data that we have collected since we were last
        rate limited.

        Args:
            data_dict (dict): dictionary of current data to write to
                output file.
            out_file (str): path to output file.

        Returns:
            dict: param dictionary, emptied.

        """
        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

        # clear dictionary so that it isn't massive in size and storing
        # data that we have already written to output
        data_dict.clear()
        self.__sleep_extractor()

        return data_dict

    # ----------------------------------------------------------------------
    # IMPORTANT: Public API
    #
    # Top-level actors are listed above their helper functions.
    # If a helper is capable of being used by more than one,
    # it will be listed above this heading.
    # ----------------------------------------------------------------------
    def get_repo_issues_data(self) -> None:
        """
        Gather all chosen data points from chosen issue numbers.

        This method is our access point into the GitHub API, the
        primary tool afforded by the Extractor class to the user.

        Raises:
            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, dump collected data to
                output file and sleep the program until calls
                can be made again.
        """
        out_data: dict = {}
        out_file: str = self.get_cfg_val("output_path")
        issue_cfg: dict = self.get_cfg_val("repo_data")
        paged_list = self.repo_metadata["paged_list"]
        issue_num_range: list = issue_cfg["range"]
        index: int = self.__get_api_obj_by_num(paged_list, issue_num_range[0])

        print(f"{TAB}Beginning issue extraction. This may take a moment...\n")
        cur_issue = paged_list[index]

        while cur_issue.number < issue_num_range[-1] + 1:
            try:
                # get issue data
                cur_issue_dict = self.__get_item_data(
                    issue_opts, "issue", cur_issue
                )

                # get issue as a PR, if it exists, and get its data
                cur_issue_pr_dict = self.__get_issue_pr(issue_opts, cur_issue)

                # retrieve issue comments
                cur_issue_comments_dict = self.__get_issue_comments(
                    issue_opts, cur_issue
                )

                # merge the PR and issue comment dicts with the issue dict
                for entry in (cur_issue_pr_dict, cur_issue_comments_dict):
                    cur_issue_dict = dict_utils.merge_dicts(
                        cur_issue_dict, entry
                    )

                cur_total_entry = {str(cur_issue.number): cur_issue_dict}

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(out_data, out_file)

            else:
                out_data = dict_utils.merge_dicts(out_data, cur_total_entry)

                print(f"{CLR}{TAB * 2}", end="")
                print(f"Issue: {cur_issue.number}, ", end="")
                print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")

                index += 1
                cur_issue = paged_list[index]

        file_io_utils.write_merged_dict_to_jsonfile(out_data, out_file)

        print()

    def __get_issue_comments(self, datatype_dict: dict, issue_obj):
        """
        Create a dict of issue comment data for the given issue param.

        If the user chose to ask the API for data about issue comments,
        get a paginated list of comments from an issue, get the desired
        data from them, and return a dict of that data.

        Args:
            datatype_dict(dict): dict of fields to get for issues from cfg.
            issue_obj (Github.Issue): issue to get comment data from.

        Returns:
            dict|None: If the user does not ask for comment data,
            return None. Else, attempt to gather comment data points.
        """
        item_type = "comments"

        # dict will hold data related to all comments for an
        # issue. Issue to comments is a one to many relationship
        comment_index = 0
        cur_comment: dict = {}

        for comment in issue_obj.get_comments():
            cur_entry = self.__get_item_data(datatype_dict, item_type, comment)

            cur_entry = {str(comment_index): cur_entry}

            cur_comment = dict_utils.merge_dicts(cur_comment, cur_entry)

            comment_index += 1

        return {item_type: cur_comment}

    def __get_issues_paged_list(self, issues_opts_dict: dict):
        """
        Retrieve and store a paginated list from GitHub.

        Raises:
            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, sleep the program until
                calls can be made again and continue attempt to
                collect desired paginated list.

            github.UnknownObjectException: this exception is
                thrown at least when a repository is not
                accessible. This is can occur because the repo
                is private or does not exist, but may occur
                for other, unforeseen reasons.

        Returns:
            github.PaginatedList of github.Issue.
        """
        while True:
            try:
                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state=state
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            else:
                return issues_paged_list

    def __get_issue_pr(self, issue_opts: dict, issue_obj):
        """
        Check if an issue is a PR and, if so, collect it's PR data.

        Args:
            issue_obj (GitHub.Issue): issue to check for PR data.

        Raises:
            github.UnknownObjectException: if the given issue is not
                also a PR, the as_pull_request() method will fail and
                raise this error. In that case, we needn't do anything.

        Returns:
            dict|None: if the issue is also a PR, return a dict of
            PR info. Else, return None.
        """
        try:
            cur_pr = issue_obj.as_pull_request()

        except github.UnknownObjectException:
            # Not a PR, does not need to raise an error.
            # return up and keep going
            return None

        else:
            # return dict of PR data
            return self.__get_pr_datum(cur_pr, issue_opts)

    def __get_pr_datum(self, cur_pr, issue_opts: dict) -> dict:
        """
        Retrieve data for a single PR and return it in a dictionary.

        Args:
            cur_pr (github.PullRequest): PR to gather data for.

        Returns:
            dict: dictionary containing data from PR parameter.
        """

        def __get_commit_data(datatype_dict, pr_obj):
            """
            Return the last commit from a paginated list of commits from a PR.

            Args:
                pr_obj (github.PullRequest): PR to gather data for.

            Returns:
                Github.Commit: last commit made in PR.

            """
            cur_commits = pr_obj.get_commits()
            commit_index = 0
            pr_commit_data = {}

            for commit in cur_commits:
                if len(commit.files) > 0:
                    commit_datum = self.__get_item_data(
                        datatype_dict, "commit", commit
                    )

                else:
                    commit_datum = {}

                pr_commit_data = dict_utils.merge_dicts(
                    pr_commit_data, {str(commit_index): commit_datum}
                )

                commit_index += 1

            return {"commits": pr_commit_data}

        item_type = "pr"
        is_merged = cur_pr.merged
        is_valid_pr = is_merged or issue_opts["state"] == "open"

        # create dict to build upon. This variable will later become
        # the val of a dict entry, making it a subdictionary
        cur_pr_dict = {"pr_merged": is_merged}

        if is_valid_pr:
            cur_pr_data = {}
            commit_data = {}

            # if the current PR is merged or is in the list of open PRs, we are
            # interested in it. Closed and unmerged PRs are of no help to the
            # project
            cur_pr_data = self.__get_item_data(issue_opts, item_type, cur_pr)

            commit_data = __get_commit_data(issue_opts, cur_pr)

            for data_dict in (cur_pr_data, commit_data):
                cur_pr_dict = dict_utils.merge_dicts(cur_pr_dict, data_dict)

        # use all gathered entry data as the val for the PR num key
        return {item_type: cur_pr_dict}

    def __get_api_obj_by_num(self, paged_list, api_obj_num: int) -> int:
        """
        Find start and end indices of API items in paginated list of items.

        Sanitize our range values so that they are guaranteed to be safe,
        find the indices of those values inside of the paginated list,
        and return

        Args:
            paged_list (Github.PaginatedList of Github.Issue): paginated
                list of issues

        Returns:
            list[int]: list of starting and ending indices for desired
                API items.
        """

        def bin_search_in_list(val: int, paged_list, last_page_index: int):
            """
            Find the index of a page in paginated list of API items.

            Iterative binary search which finds the page of an API item,
            such as a PR or issue, inside of a list of pages of related
            objects from the GitHub API.

            Args:
                paged_list(Github.PaginatedList of Github.Issue): paginated
                    list of issues
                last_page_index (int): index of last page in paginated list
                val (int): number of item in list that we desire; e.g. PR# 800

            Returns:
                int: index of page in given paginated listwhere val
                param is located
            """
            low = 0
            high = last_page_index

            while low < high - 1:
                mid = (low + high) // 2

                mid_page = paged_list.get_page(mid)
                mid_first_val = mid_page[0].number
                mid_last_val = mid_page[-1].number

                # if the value we want is greater than the first item
                # (cur_val - page_len) on the middle page but less
                # than the last item, it is in the middle page
                if mid_first_val <= val <= mid_last_val:
                    return mid_page

                if val < mid_first_val:
                    high = mid - 1

                elif val > mid_last_val:
                    low = mid + 1

            return paged_list.get_page(low)

        def bin_search_in_page(val: int, page, page_len: int) -> int:
            """
            Find the index of an API item in a page of API items.

            Iterative binary search modified to return either the exact
            index of the item with the number the user desires or the
            index of the item beneath that value in the case that the
            value does not exist in the list. An example might be that
            a paginated list of issues does not have #'s 9, 10, or 11,
            but the user wants to begin looking for data at #10. This
            binary search should return the index of the API object
            with the number 8.

            Args:
                val (int): value to look for in page parameter
                paged_list_page (page of Github.Issue): a single page
                    from paginated list of issues
                page_len (int): length of pages in paginated lists for
                    this validated GitHub session

            Returns:
                int: index of the object we are looking for
            """
            low = 0

            # because this binary search is looking through lists that
            # may have items missing, we want to be able to return the
            # index of the nearest item before the item we are looking
            # for. Therefore, we stop when low is one less than high.
            # This allows us to take the lower value when a value does
            # not exist in the list.
            while low < page_len - 1:
                mid = (low + page_len) // 2

                cur_val = page[mid].number

                if val == cur_val:
                    return mid

                if val < cur_val:
                    page_len = mid - 1

                elif val > cur_val:
                    low = mid + 1

            return low

        print(f"{TAB}Finding index of first item in range...")

        # use binary search to find the page inside of the
        # list of pages that contains the item number of interest
        found_page = bin_search_in_list(
            api_obj_num, paged_list, self.repo_metadata["last_page_index"]
        )

        # use iterative binary search to find item of interest in found page
        return bin_search_in_page(api_obj_num, found_page, len(found_page))
