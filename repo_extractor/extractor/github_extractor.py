"""The github_extractor module provides and exposes functionality to mine GitHub repositories."""

import datetime
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
    """The Extractor class contains and executes GitHub REST API functionality."""

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
        self.__set_output_file_dict_val()

        # initialize authenticated GitHub session
        self.gh_sesh = _sessions.GithubSession(self.get_cfg_val("auth_file"))

        self.repo_obj = self.__get_repo_obj()

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
                print(f'{TAB}Repo "{job_repo}" either does not exist or is private!')
                sys.exit(1)

            else:
                return repo_obj

    def __set_output_file_dict_val(self):
        """Create and set output directory and file paths."""
        out_dir = self.get_cfg_val("output_dir")

        # lop repo str off of full repo info, e.g. owner/repo
        repo_title = self.get_cfg_val("repo").rsplit("/", 1)[1]

        out_path = file_io_utils.mk_json_outpath(out_dir, repo_title, "issues")

        self.cfg.set_cfg_val("output_file", out_path)

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

    def __get_commit_datum(self, commit_opts: dict, cur_commit):
        """
        Retrieve data for a single commit and return it in a dictionary.

        Wrapper around API getter engine.

        Args:
            cur_commit (github.Commit): commit to gather data for.

        Returns:
            dict: dictionary containing data from commit parameter.

            key = commit SHA
            val = commit data
        """
        cur_commit_data = self.__get_item_data(commit_opts, "commit", cur_commit)

        return {cur_commit.sha: cur_commit_data}

    @staticmethod
    def __get_item_data(category_dict: dict, field_type: str, cur_item) -> dict:
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

            print(f"{CLR}{TAB * 2}Time until limit reset: {cntdown_str}", end="\r")

            # sleep for a while
            time.sleep(1)
            cntdown_time -= 1

        print(f"{CLR}{TAB * 2}Starting data collection...", end="\r")

    def __update_output_json_for_sleep(self, data_dict: dict, out_file: str) -> dict:
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
    # Public API
    #
    # Top-level actors are listed above their helper functions.
    # If a helper is capable of being used by more than one,
    # it will be listed above this heading.
    # ----------------------------------------------------------------------

    # COMMIT ACCESS POINT #
    def get_repo_commit_data(self) -> None:
        """
        Create a dict of contributors and their contributions.

        The project is interested in determining the core contributors for
        a given repository. To do this, we have implemented the algorithm
        discussed in Coelho et al., 2018 (see citation below) wherein the
        contributors whose sum commits are 80% of the total commits for the
        repo are aggregated and those who have less than five commits are
        disregarded. This implementation is found in the OSL metrics
        aggregator. This method creates a dict of all contributors,
        descendingly ordered by total commits, for input into the Coelho
        et al. custom "Commit-Based Heuristic" algorithm.

        Citations:
            Coelho J, Valente MT, Silva LL, Hora A (2018) Why we engage in
            floss: Answers from core developers. In: Proceedings of the 11th
            International Workshop on Cooperative and Human Aspects of
            Software Engineering, pp 114–121

            link: https://arxiv.org/pdf/1803.05741.pdf
        """

        def __get_dev_num_contribs(commits, total_num_commits: int, out_file: str):
            """
            TODO.

            Args:
                num_commits ():

            Returns:
                dict: sorted dictionary of (contributor: contributions) pairs
            """
            contrib_dict = {}
            i = 0
            print(f"{TAB * 2}total: {total_num_commits}")

            while i < total_num_commits:
                try:
                    author = commits[i].commit.author.name

                    if author not in contrib_dict:
                        contrib_dict[author] = 1

                    else:
                        contrib_dict[author] += 1

                except github.RateLimitExceededException:
                    self.__update_output_json_for_sleep(contrib_dict, out_file)

                else:
                    print(f"{CLR}{TAB * 2}", end="")
                    print(f"index: {i}, ", end="")
                    print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")
                    i += 1

            print("\n")

            return dict(sorted(contrib_dict.items(), key=lambda x: x[1], reverse=True))

        contrib_opts: dict = self.cfg.cfg_dict["repo_data"]["by_commit"][
            "dev_contributions"
        ]

        strttm_list = contrib_opts["start"]
        freq_list = contrib_opts["frequency"]
        out_file: str = self.get_cfg_val("output_file")

        start_tm = datetime.datetime(
            strttm_list[0], strttm_list[1], strttm_list[2], 0, 0, 0
        )

        cur_entry = {}
        data_dict = {}

        while start_tm < datetime.datetime.now():
            try:
                # get the current starting time plus the user-defined
                # frequency. This will be the end date of the current
                # request for a paginated list of commits.
                start_tm_next = start_tm + datetime.timedelta(
                    weeks=freq_list[0], days=freq_list[1]
                )

                print(f"{TAB}{start_tm} - {start_tm_next}")

                # get commits to process
                cur_commit_list = self.__get_commits_paged_list(start_tm, start_tm_next)
                total_commits = cur_commit_list.totalCount

                cur_entry["num_commits"] = total_commits

                # process commits
                cur_entry["contributions"] = __get_dev_num_contribs(
                    cur_commit_list, total_commits, out_file
                )

                for date_obj in [start_tm_next, start_tm]:
                    date_key = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
                    cur_entry = {date_key: cur_entry}

                start_tm = start_tm_next

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(data_dict, out_file)

            else:
                # merge it to the total dict
                data_dict = dict_utils.merge_dicts(data_dict, cur_entry)
                cur_entry.clear()

        # nest commit data in appropriate label
        data_dict = {"by_commit": data_dict}

        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

    def __get_commits_paged_list(self, start, end):
        """
        Retrieve and store a paginated list of commits from GitHub.

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
            github.PaginatedList of github.Commit.
        """
        while True:
            try:
                commits_paged_list = self.repo_obj.get_commits(since=start, until=end)

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            else:
                return commits_paged_list

    # ISSUE ACCESS POINT #
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
        out_file = self.get_cfg_val("output_file")
        issue_opts: dict = self.cfg.cfg_dict["repo_data"]["by_issue"]
        paged_list = self.__get_issues_paged_list(issue_opts)
        # get indices of sanitized range values
        range_list: list[int] = self.__get_range_api_indices(paged_list, issue_opts)

        data_dict = {}
        start_val = range_list[0]

        print(f"{TAB}Beginning issue extraction. This may take a moment...\n")

        while start_val < range_list[1] + 1:
            try:
                cur_issue = paged_list[start_val]

                # get issue data
                cur_issue_dict = self.__get_item_data(issue_opts, "issue", cur_issue)

                # get issue as a PR, if it exists, and get its data
                cur_issue_pr_dict = self.__get_issue_pr(issue_opts, cur_issue)

                # retrieve issue comments
                cur_issue_comments_dict = self.__get_issue_comments(
                    issue_opts, cur_issue
                )

                # merge the PR and issue comment dicts with the issue dict
                for entry in (cur_issue_pr_dict, cur_issue_comments_dict):
                    cur_issue_dict = dict_utils.merge_dicts(cur_issue_dict, entry)

                cur_total_entry = {str(cur_issue.number): cur_issue_dict}

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(data_dict, out_file)

            else:
                data_dict = dict_utils.merge_dicts(data_dict, cur_total_entry)

                print(f"{CLR}{TAB * 2}", end="")
                print(f"Issue: {cur_issue.number}, ", end="")
                print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")

                start_val += 1

        data_dict = {"by_issue": data_dict}
        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

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
        cur_comment_dict = {}

        for comment in issue_obj.get_comments():
            cur_entry = self.__get_item_data(datatype_dict, item_type, comment)

            cur_entry = {str(comment_index): cur_entry}

            cur_comment_dict = dict_utils.merge_dicts(cur_comment_dict, cur_entry)

            comment_index += 1

        return {item_type: cur_comment_dict}

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
        item_state = issues_opts_dict["state"]

        while True:
            try:
                issues_paged_list = self.repo_obj.get_issues(
                    direction="asc", sort="created", state=item_state
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

        def __get_last_commit(datatype_dict, pr_obj):
            """
            Return the last commit from a paginated list of commits from a PR.

            Args:
                pr_obj (github.PullRequest): PR to gather data for.

            Returns:
                Github.Commit: last commit made in PR.

            """
            last_commit_data = {}
            data_type = "commit"

            # get paginated list of commits for PR at current index
            commit_list = pr_obj.get_commits()

            last_commit = commit_list[commit_list.totalCount - 1]

            if len(last_commit.files) > 0:

                # get all data from that commit
                last_commit_data = self.__get_commit_datum(datatype_dict, last_commit)

            return {data_type: last_commit_data}

        item_type = "pr"
        is_merged = cur_pr.merged
        is_valid_pr = is_merged or issue_opts["state"] == "open"

        # create dict to build upon. This variable will later become
        # the val of a dict entry, making it a subdictionary
        cur_pr_dict = {"pr_merged": is_merged}

        if is_valid_pr:
            cur_pr_data = {}
            last_commit_data = {}

            # if the current PR is merged or is in the list of open PRs, we are
            # interested in it. Closed and unmerged PRs are of no help to the
            # project
            cur_pr_data = self.__get_item_data(issue_opts, item_type, cur_pr)

            last_commit_data = __get_last_commit(issue_opts, cur_pr)

            for data_dict in (cur_pr_data, last_commit_data):
                cur_pr_dict = dict_utils.merge_dicts(cur_pr_dict, data_dict)

        # use all gathered entry data as the val for the PR num key
        return {item_type: cur_pr_dict}

    def __get_range_api_indices(self, paged_list, issue_opts_dict: dict) -> list:
        """
        Find start and end indices of API items in paginated list of items.

        Sanitize our range values so that they are guaranteed to be safe,
        find the indices of those values inside of the paginated list,
        and return

        Args:
            paged_list (Github.PaginatedList of Github.Issue): paginated
                list of issues

        Returns:
            list[int]: list of starting and ending indices for desired API items
        """

        def __bin_search_in_list(paged_list, last_page_index: int, val: int) -> int:
            """
            Find the index of a page of an API item in paginated list of API items.

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

                mid_first_val = paged_list.get_page(mid)[0].number
                mid_last_val = __get_page_last_item(paged_list, mid).number

                # if the value we want is greater than the first item
                # (cur_val - page_len) on the middle page but less
                # than the last item, it is in the middle page
                if mid_first_val <= val <= mid_last_val:
                    return mid

                if val < mid_first_val:
                    high = mid - 1

                elif val > mid_last_val:
                    low = mid + 1

            return low

        def __bin_search_in_page(val: int, paged_list_page, page_len: int) -> int:
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

                cur_val = paged_list_page[mid].number

                if val == cur_val:
                    return mid

                if val < cur_val:
                    page_len = mid - 1

                elif val > cur_val:
                    low = mid + 1

            return low

        def __get_issue_num_paginated_index(
            issue_num: int, last_page_index: int, page_len: int
        ) -> int:
            """
            Find the index of the issue with the given number in list of issues.

            GitHub obviously cannot ensure that issue indices match
            with issue numbers. We have to account for missing items
            and page lengths when searching for an item.

            Note:
                This function and the associated functions are pretty
                slow. They would benefit a lot from optimization and a
                faster fetching mechanism. PyGithub has a private method
                that can actually be accesed but this is firstly abusive
                of its purpose and, secondly, seems to be the method that
                is slow under the hood of this method. See __fetchToIndex()
                in https://github.com/PyGithub/PyGithub/blob/master/github/PaginatedList.py

            Args:
                issue_num (int): issue number to search for
                last_page_index (int): index of the last page in the
                    paginated list
                page_len (int): length of pages in paginated lists for
                    this validated GitHub session

            Returns:
                int: index of a user-specified issue number in paginated
                list of issues
            """
            # use binary search to find the index of the page inside
            # of the list of pages that contains the item number, e.g.
            # PR# 600, that we want
            page_index = __bin_search_in_list(paged_list, last_page_index, issue_num)

            found_page = paged_list.get_page(page_index)

            # use iterative binary search to find item in correct page
            # of linked list
            item_page_index = __bin_search_in_page(
                issue_num, found_page, len(found_page)
            )

            # the index of the item in the total list is the page index
            # that it is on multiplied by the amount of items per page,
            # summed with the index of the item in the page, e.g. if
            # the item is on index 20 of page 10 and there are 30
            # items per page, its index in the list is 20 + (10 * 30)
            item_list_index = item_page_index + (page_index * page_len)

            # the index of the items we need is the amount of items per page
            # that were skipped plus the index of the item in it's page
            return item_list_index

        def __get_page_last_item(paged_list, page_index: int):
            try:
                last_item = paged_list.get_page(page_index)[-1]

            except IndexError:
                print("There are no issues of the specified type in this repo!")
                sys.exit(1)

            else:
                return last_item

        def __get_sanitized_range_vals(
            range_list: list[int], last_page_index: int
        ) -> list[int]:
            """
            Sanitize the given issue number pair so that they are in bounds.

            The user configuration allows the user to choose the
            range of issues they would like to mine. This config
            entry will be guaranteed to be a list of two numbers
            above 0 by Cerberus, but the numbers can be anything
            above that. We must make sure before we begin to mine
            that both numbers in the issue number range are less
            than the maximum issue number for our chosen type, e.g.
            closed, in the repository.

            Args:
                range_list (list[int]): list of issue numbers to
                    sanitize. Will have an enforced length of two.
                last_page_index (int): index of last page in paginated
                    list of issues.

            Returns:
                list[int]: list of sanitized issue numbers.
            """
            # get the highest item num in the paginated list of items,
            # e.g. very last PR num
            highest_num = __get_page_last_item(paged_list, last_page_index).number

            # get sanitized range. This will correct any vals given in
            # the range cfg so that they are within the values that are
            # in the paged list. We are protected from too low of values
            # by the Cerberus config schema, so this process only looks
            # at values that are too high.
            clean_range_tuple = [
                min(val, highest_num) for val in (range_list[0], range_list[-1])
            ]

            return clean_range_tuple

        out_list = []
        page_len = self.gh_sesh.get_pg_len()

        # get index of last page in paginated list
        last_page_index = (paged_list.totalCount - 1) // page_len

        print(f"{TAB}Sanitizing range configuration values...")

        clean_range_list = __get_sanitized_range_vals(
            issue_opts_dict["range"], last_page_index
        )

        print(f"{TAB}finding start and end indices corresponding to range values...")

        # for the two boundaries in the sanitized range
        for val in clean_range_list:
            val_index = __get_issue_num_paginated_index(val, last_page_index, page_len)
            out_list.append(val_index)

            print(
                f"{TAB * 2}item #{val} found at index {val_index} in the paginated list..."
            )

        print()

        return out_list
