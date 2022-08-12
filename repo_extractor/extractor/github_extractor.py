"""Exposes functionality to mine GitHub repositories."""

import sys
import time
import traceback
import github
from repo_extractor import conf, schema
from repo_extractor.utils import dict_utils, file_io_utils as io
from repo_extractor.extractor import _sessions

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

        # create output path in fs so that it is already ready for work.
        # The JSON writing functionality will check if it exists later
        # and create it again if something happened to it during execution,
        # attempting to circumvent TOCTOU errors that will crash execution.
        # Because this program can be very long-running, multiple checks
        # and inits are smart because the filesystem can change.
        io.mk_json_outpath(self.cfg.get_cfg_val("output_path"))

        # initialize authenticated GitHub session
        self.gh_sesh = _sessions.GithubSession(
            self.cfg.get_cfg_val("auth_path")
        )

        self.paged_list = self.__get_issues_paged_list(
            self.__get_repo_obj(), self.cfg.get_cfg_val("state")
        )

        # get index of last page in paginated list
        self.last_page_index: int = (
            self.paged_list.totalCount - 1
        ) // self.gh_sesh.get_pg_len()

        self.cfg.set_cfg_val("range", self.__get_sanitized_cfg_range())

    def __get_repo_obj(self):
        """
        TODO.

        Returns:
            github.Repository.Repository: repo obj for current extraction op
        """
        job_repo = self.cfg.get_cfg_val("repo")

        while True:
            try:
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

    def __get_sanitized_cfg_range(self) -> tuple:

        print(f"{TAB}Sanitizing range...")

        range_list: list[int] = self.cfg.get_cfg_val("range")

        # get the highest item num in the paginated list of items,
        # e.g. very last PR num
        last_page = self.paged_list.get_page(self.last_page_index)
        last_num: int = last_page[-1].number
        print(f"{TAB * 2}Last item number: {last_num}")

        # get sanitized range. This will correct any vals given in
        # the range cfg so that they are within the values that are
        # in the paged list. We are protected from too low of values
        # by the Cerberus config schema, so this process only looks
        # at values that are too high.
        sani_range: tuple[int, ...] = tuple(
            min(last_num, val) for val in range_list
        )

        print(f"{TAB * 2}Range cleaned: {sani_range[0]} to {sani_range[-1]}")

        return sani_range

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    @staticmethod
    def __get_item_data(fields: list, cmd_tbl: dict, cur_item) -> dict:
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
        # when called, this will resolve to various function calls, e.g.
        # "body": cmd_tbl["body"](cur_PR)
        return {field: cmd_tbl[field](cur_item) for field in fields}

    def __sleep_extractor(self) -> None:
        """Sleep the program until we can make calls again."""
        cntdwn_time = self.gh_sesh.get_remaining_ratelimit_time()

        while cntdwn_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(cntdwn_time, 60)

            # format the time string before printing
            cntdown_str = f"{minutes:02d}:{seconds:02d}"

            print(
                f"{CLR}{TAB * 2}Time until limit reset: {cntdown_str}",
                end="\r",
            )

            # sleep for a while
            time.sleep(1)
            cntdwn_time -= 1

        print(f"{CLR}{TAB * 2}Starting data collection...", end="\r")

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
        func_schema: dict = {
            "issues": self.__get_item_data,
            "commits": self.__get_issue_commits,
            "comments": self.__get_issue_comments,
        }

        out_data: dict = {}
        output_file: str = self.cfg.get_cfg_val("output_path")
        issue_range: list = self.cfg.get_cfg_val("range")

        start_index: int = self.__get_issue_index_by_num(
            self.paged_list, issue_range[0]
        )
        end_index: int = self.__get_issue_index_by_num(
            self.paged_list, issue_range[-1]
        )

        print(
            f"{TAB}Starting issue mining at #{issue_range[0]}. Please wait..."
        )

        while start_index < end_index + 1:
            cur_item_data: dict = {}
            cur_issue_data: dict = {}

            cur_issue = self.paged_list[start_index]

            try:
                for key, func in func_schema.items():
                    if self.cfg.get_cfg_val(key):
                        cur_item_data = func(
                            self.cfg.get_cfg_val(key),
                            schema.cmd_tbl[key],
                            cur_issue,
                        )

                        cur_issue_data = dict_utils.merge_dicts(
                            cur_issue_data, cur_item_data
                        )

                cur_total_entry = {str(cur_issue.number): cur_issue_data}

            except github.RateLimitExceededException:
                io.write_merged_dict_to_jsonfile(out_data, output_file)

                # clear dictionary so that it isn't massive and
                # holding onto data that we have already written
                # to output
                out_data.clear()
                self.__sleep_extractor()

            except KeyboardInterrupt:
                io.write_merged_dict_to_jsonfile(out_data, output_file)
                print(f"\n\n{TAB}Terminating at item #{cur_issue.number}\n")
                sys.exit(1)

            else:
                out_data = dict_utils.merge_dicts(out_data, cur_total_entry)

                print(f"{CLR}{TAB * 2}", end="")
                print(f"Issue: {cur_issue.number}, ", end="")
                print(
                    f"calls: {self.gh_sesh.get_remaining_calls()}",
                    end="\r",
                )

                start_index += 1

        io.write_merged_dict_to_jsonfile(out_data, output_file)

        print()

    def __get_issue_comments(self, fields: list, cmd_tbl: dict, issue) -> dict:
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
        comment_index: int = 0
        cur_comment_data: dict = {}

        for comment in issue.get_comments():
            cur_entry = self.__get_item_data(fields, cmd_tbl, comment)

            cur_entry = {str(comment_index): cur_entry}

            cur_comment_data = dict_utils.merge_dicts(
                cur_comment_data, cur_entry
            )

            comment_index += 1

        return {item_type: cur_comment_data}

    def __get_issue_commits(self, fields: list, cmd_tbl: dict, issue) -> dict:
        """TODO."""

        def get_as_pr(cur_issue):
            try:
                cur_pr = cur_issue.as_pull_request()

            except github.UnknownObjectException:
                # Not a PR, does not need to raise an error.
                # Return up and keep going
                return None

            else:
                return cur_pr

        def __get_commit_data(pr_obj):
            """
            Return the last commit from a paginated list of commits from a PR.

            Args:
                pr_obj (github.PullRequest): PR to gather data for.

            Returns:
                Github.Commit: last commit made in PR.

            """
            field_type: str = "commits"
            commit_index: int = 0
            pr_commit_data: dict = {}

            for commit in pr_obj.get_commits():
                if commit.files:
                    commit_datum = self.__get_item_data(
                        fields, cmd_tbl, commit
                    )

                else:
                    commit_datum = {}

                pr_commit_data = dict_utils.merge_dicts(
                    pr_commit_data, {str(commit_index): commit_datum}
                )

                commit_index += 1

            return {field_type: pr_commit_data}

        pr_data: dict
        pr_obj = get_as_pr(issue)

        if pr_obj is not None:
            pr_data = {
                "is_pr": True,
                "state": pr_obj.state,
                "is_merged": pr_obj.merged,
            }

            commit_data: dict = __get_commit_data(pr_obj)
            pr_data = dict_utils.merge_dicts(pr_data, commit_data)

        else:
            pr_data = {"is_pr": False}

        return pr_data

    def __get_issue_index_by_num(self, paged_list, issue_num: int) -> int:
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
            low: int = 0
            high: int = last_page_index
            mid_first_val: int
            mid_last_val: int

            while low < high:
                mid = (low + high) // 2

                mid_page = paged_list.get_page(mid)
                mid_first_val = mid_page[0].number
                mid_last_val = mid_page[-1].number

                # if the value we want is greater than the first item
                # (cur_val - page_len) on the middle page but less
                # than the last item, it is in the middle page
                if mid_first_val <= val <= mid_last_val:
                    return mid_page, mid

                if val < mid_first_val:
                    high = mid - 1

                elif val > mid_last_val:
                    low = mid + 1

            return paged_list.get_page(low), low

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
            low: int = 0
            mid: int

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

        print(f"{TAB}Finding index of item #{issue_num}...")

        # use binary search to find the page inside of the
        # list of pages that contains the item number of interest
        item_page, item_page_index = bin_search_in_list(
            issue_num, paged_list, self.last_page_index
        )

        # use iterative binary search to find item of interest in found page
        item_index: int = bin_search_in_page(
            issue_num, item_page, len(item_page)
        )

        item_index = (item_page_index * self.gh_sesh.get_pg_len()) + item_index

        print(f"{TAB * 2}Found at index {item_index}!")

        return item_index
