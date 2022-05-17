"""The github_extractor module provides and exposes functionality to mine GitHub repositories."""

import sys
import time
import github
from repo_extractor import conf, schema
from repo_extractor.extractor import _sessions
from repo_extractor.utils import dict_utils, file_io_utils


# TODO:
#   1. if you use binary search on open state items and search for issues or PRs
#   below the lowest value, it will return the lowest value, e.g. "280" for open
#   PRs on react/facebook will returns a value in the 13000's. We want to not do
#   that


# ANSI escape sequence for clearing a row in the console:
# https://stackoverflow.com/a/64245513
CLR = "\x1b[K"
TAB = " " * 4


def _get_page_last_item(paged_list, page_index: int):
    try:
        last_item = paged_list.get_page(page_index)[-1]

    except IndexError:
        print("There are no issues of the specified type in this repo!")
        sys.exit(1)

    else:
        return last_item


class Extractor:
    """The Extractor class contains and executes GitHub REST API functionality."""

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

        auth_path = self.get_cfg_val("auth_file")

        # initialize authenticated GitHub session
        self.gh_sesh = _sessions.GithubSession(auth_path)

        self.issues_paged_list = self.__get_issues_paged_list()

        self.__set_output_file_dict_val()

    def __fields_exist(self, item_type: str) -> bool:
        return len(self.get_cfg_val(f"{item_type}_fields")) > 0

    def __get_range_api_indices(self, paged_list) -> list:
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
                mid_last_val = _get_page_last_item(paged_list, mid).number

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
            highest_num = _get_page_last_item(paged_list, last_page_index).number

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
            self.get_cfg_val("range"), last_page_index
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

    def get_issues_data(self) -> None:
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
        data_dict = {}
        out_file = self.get_cfg_val("issue_output_file")

        # get indices of sanitized range values
        range_list = self.__get_range_api_indices(self.issues_paged_list)

        # unpack vals
        start_val = range_list[0]
        end_val = range_list[1]

        print(f"{TAB}Beginning issue extraction. Starting may take a moment...\n")

        while start_val < end_val + 1:
            try:
                cur_issue = self.issues_paged_list[start_val]

                # get issue data, provided in the "issues" cfg list
                cur_issue_dict = schema.get_item_data(self.cfg, "issue", cur_issue)

                # get issue as a PR if it exists
                cur_issue_pr_dict = self.__get_issue_pr(cur_issue)

                cur_issue_comments_dict = self.__get_issue_comments(cur_issue)

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

        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)
        print("\n")

    def __get_issue_comments(self, issue_obj) -> dict | None:
        """
        Create a dict of issue comment data for the given issue param.

        If the user chose to ask the API for data about issue comments,
        get a paginated list of comments from an issue, get the desired
        data from them, and return a dict of that data.

        Args:
            issue_obj (Github.Issue): issue to get comment data from.

        Returns:
            dict or None: If the user does not ask for comment data,
            return None. Else, attempt to gather comment data points.
        """
        item_type = "comments"

        if self.__fields_exist(item_type):
            # dict will hold data related to all comments for an
            # issue. Issue to comments is a one to many relationship
            comment_index = 0
            cur_issue_comment_dict = {}

            for comment in issue_obj.get_comments():
                cur_entry = schema.get_item_data(self.cfg, item_type, comment)

                cur_issue_comment_dict = dict_utils.merge_dicts(
                    cur_issue_comment_dict, {str(comment_index): cur_entry}
                )

                comment_index += 1

            return {item_type: cur_issue_comment_dict}

        return None

    def __get_issues_paged_list(self):
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
        job_repo = self.get_cfg_val("repo")
        item_state = self.get_cfg_val("state")

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state=item_state
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Repo "{job_repo}" either does not exist or is private!')
                sys.exit(1)

            else:
                return issues_paged_list

    def __get_issue_pr(self, issue_obj) -> dict | None:
        """
        Check if an issue is a PR and, if so, collect it's PR data.

        Args:
            issue_obj (GitHub.Issue): issue to check for PR data.

        Raises:
            github.UnknownObjectException: if the given issue is not
                also a PR, the as_pull_request() method will fail and
                raise this error. In that case, we needn't do anything.

        Returns:
            dict or None: if the issue is also a PR, return a dict of
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
            return self.__get_pr_datum(cur_pr)

    def __get_pr_datum(self, cur_pr) -> dict:
        """
        Retrieve data for a single PR and return it in a dictionary.

        Args:
            cur_pr (github.PullRequest): PR to gather data for.

        Returns:
            dict: dictionary containing data from PR parameter.
        """

        def __get_last_commit(pr_obj):
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
                last_commit_data = schema.get_item_data(
                    self.cfg, data_type, last_commit
                )

            return {data_type: last_commit_data}

        item_type = "pr"
        is_merged = cur_pr.merged
        is_valid_pr = is_merged or self.get_cfg_val("state") == "open"

        # create dict to build upon. This variable will later become
        # the val of a dict entry, making it a subdictionary
        cur_pr_dict = {"pr_merged": is_merged}

        if is_valid_pr:
            cur_pr_data = {}
            last_commit_data = {}

            # if the current PR is merged or is in the list of open PRs, we are
            # interested in it. Closed and unmerged PRs are of no help to the
            # project
            if self.__fields_exist(item_type):
                cur_pr_data = schema.get_item_data(self.cfg, item_type, cur_pr)

            if self.__fields_exist("commit"):
                last_commit_data = __get_last_commit(cur_pr)

            for data_dict in (cur_pr_data, last_commit_data):
                cur_pr_dict = dict_utils.merge_dicts(cur_pr_dict, data_dict)

        # use all gathered entry data as the val for the PR num key
        return {item_type: cur_pr_dict}

    def __set_output_file_dict_val(self):
        """Create and set output directory and file paths."""
        out_dir = self.get_cfg_val("output_dir")

        # lop repo str off of full repo info, e.g. owner/repo
        repo_title = self.get_cfg_val("repo").rsplit("/", 1)[1]

        out_path = file_io_utils.mk_json_outpath(out_dir, repo_title, "issues")

        self.cfg.set_cfg_val("issue_output_file", out_path)

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

        print("Restarting data collection...", end="\r")

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
