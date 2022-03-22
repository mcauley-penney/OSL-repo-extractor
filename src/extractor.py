"""
The extractor module provides and exposes functionality to mine GitHub repositories.
"""

import github
from src import conf, file_io, schema, sessions


def _get_page_last_item(paged_list, page_index):
    return paged_list.get_page(page_index)[-1]


def _merge_dicts(base: dict, to_merge: dict) -> dict:
    """
    Merge two dictionaries
    NOTES:
        • syntax in 3.9 or greater is "base |= to_merge"
            • pipe is the "merge" operator, can be used in augmented assignment

    :param base: dict to merge into
    :type base: dict
    :param to_merge: dict to dissolve into base dict
    :type to_merge: dict
    :return: base dict
    :rtype: dict
    """
    return {**base, **to_merge}


class Extractor:
    """
    The Extractor class contains and executes GitHub REST API functionality. It
    initiates and holds onto an object that stores the configuration for the program
    execution, an object that initiates and contains a connection to the GitHub API, and
    an object that writes content to JSON files.
    """

    def __init__(self, cfg_path) -> None:
        """
        Initialize an extractor object. This object is our top-level actor and must be
        used by the user to extract data, such as in a driver program
        """
        # read configuration dictionary from input configuration file
        cfg_dict = file_io.read_json_to_dict(cfg_path)

        # initialize configuration object with cfg dict
        self.cfg = conf.Cfg(cfg_dict, schema.cfg_schema)

        auth_path = self.get_cfg_val("auth_file")

        # initialize authenticated GitHub session
        self.gh_sesh = sessions.GithubSession(auth_path)

        self.paged_list_dict = self.__get_paged_list_dict()

    def _get_range_api_indices(self, paged_list) -> list:
        """
        sanitize our range values so that they are guaranteed to be safe, find the
        indices of those values inside of the paginated list, and return

        :param paged_list; Github.PaginatedList of Github.Issues or Github.PullRequests:
            list of API objects

        :param range_list list[int]: list of range beginning and end values that we wish
        to find in the given paginated list

        :rtype int: list of indices to the paginated list of items that we wish to find
        """

        def __bin_search_in_list(paged_list, last_page_index: int, val: int) -> int:
            """
            iterative binary search which finds the page of an item that we are looking
            for, such as a PR or issue, inside of a list of pages of related objects
            from the GitHub API.

            :param paged_list: paginated list of issues or PRs
            :type paged_list:Github.PaginatedList of Github.Issues or
            Github.PullRequests
            :param val: number of item in list that we desire; e.g. PR# 800
            :type val: int
            :return: index of page in paginated list param where val param is located
            :rtype: int
            """
            low = 0
            high = last_page_index

            while low < high - 1:
                mid = (low + high) // 2

                mid_first_val = paged_list.get_page(mid)[0].number
                mid_last_val = _get_page_last_item(paged_list, mid).number

                # if the value we want is greater than the first item (cur_val -
                # page_len) on the middle page but less than the last item, it is in
                # the middle page
                if mid_first_val <= val <= mid_last_val:
                    return mid

                if val < mid_first_val:
                    high = mid - 1

                elif val > mid_last_val:
                    low = mid + 1

            return low

        def __bin_search_in_page(paged_list_page, page_len: int, val: int) -> int:
            """
            iterative binary search modified to return either the exact index of the
            item with the number the user desires or the index of the item beneath that
            value in the case that the value does not exist in the list. An example
            might be that a paginated list of issues does not have #'s 9, 10, or 11, but
            the user wants to begin looking for data at #10. This binary search should
            return the index of the API object with the number 8.

            :param paged_list_page PaginatedList[Github.Issues|Github.PullRequests]:
                list of API objects

            :param val int: the value that we wish to find the index of, e.g. the index
            of PR #10

            :rtype int: index of the object we are looking for
            """
            low = 0

            # because this binary search is looking through lists that may have items
            # missing, we want to be able to return the index of the nearest item before
            # the item we are looking for. Therefore, we stop when low is one less than
            # high. This allows us to take the lower value when a value does not exist
            # in the list.
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

        range_list = self.get_cfg_val("range")
        page_len = self.gh_sesh.get_pg_len()
        out_list = []

        print(f"{' ' * 4}Sanitizing range configuration values...")

        # get index of last page in paginated list
        last_page_index = (paged_list.totalCount - 1) // page_len

        # get the highest item num in the paginated list of items, e.g. very last PR num
        highest_num = _get_page_last_item(paged_list, last_page_index).number

        # get sanitized range. This will correct any vals given in the range cfg so that
        # they are within the values that are in the paged list. We are protected from
        # too low of values by the Cerberus config schema, so this process only looks at
        # values that are too high.
        clean_range_tuple = (
            min(val, highest_num) for val in (range_list[0], range_list[-1])
        )

        print(
            f"{' ' * 4}finding start and end indices corresponding to range values..."
        )

        # for the two boundaries in the sanitized range
        for val in clean_range_tuple:

            # use binary search to find the index of the page inside of the list of
            # pages that contains the item number, e.g. PR# 600, that we want
            page_index = __bin_search_in_list(paged_list, last_page_index, val)

            found_page = paged_list.get_page(page_index)

            # use iterative binary search to find item in correct page of linked list
            item_page_index = __bin_search_in_page(found_page, len(found_page), val)

            # the index of the item in the total list is the page index that it is on
            # multiplied by the amount of items per page, summed with the index of the
            # item in the page, e.g. if the item is on index 20 of page 10 and there are
            # 30 items per page, its index in the list is 20 + (10 * 30)
            item_list_index = item_page_index + (page_index * page_len)

            print(
                f"{' ' * 8}item #{val} found at index {item_list_index} in the paginated list..."
            )

            # the index of the items we need is the amount of items per page
            # that were skipped plus the index of the item in it's page
            out_list.append(item_list_index)

        print()

        return out_list

    def get_cfg_val(self, key: str):
        """
        :param key: key of desired value from configuration dict to get
        :type key: str
        :return: value from configuration associated with given key
        :rtype: [str | int]
        """
        return self.cfg.get_cfg_val(key)

    def get_issues_data(self) -> None:
        """
        retrieves issue data from the GitHub API; uses the "range"
        configuration value to determine what indices of the issue paged list
        to look at and the "issues_fields" field to determine what information
        it should retrieve from each issues of interest

        :raises github.RateLimitExceededException: if rate limited by the
        GitHub REST API, dump collected data to output file and sleep the
        program until calls can be made again
        """

        data_type = "issue"
        data_dict = {data_type: {}}
        out_file = self.get_cfg_val("output_file")
        paged_list = self.__get_paged_list(data_type)

        # get indices of sanitized range values
        range_list = self._get_range_api_indices(paged_list)

        # unpack vals
        start_val = range_list[0]
        end_val = range_list[1]

        print(f"{' ' * 4}Beginning issue extraction. Starting may take a moment...\n")

        while start_val < end_val + 1:
            try:
                cur_issue = paged_list[start_val]

                cur_item_data = self.__get_item_data(data_type, cur_issue)

                cur_entry = {str(cur_issue.number): cur_item_data}

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(data_dict, out_file)

            else:
                data_dict[data_type] = _merge_dicts(data_dict[data_type], cur_entry)
                self.gh_sesh.print_rem_gh_calls()

                start_val += 1

        file_io.write_merged_dict_to_json(data_dict, out_file)

    def __get_item_data(self, item_type, cur_item) -> dict:
        """
        For each field in the list provided by the user in configuration, e.g.
        "issue_fields", get the associated piece of data and store it in a
        dict where {field name: field data}, e.g. {"issue number": 20}

        :param item_type: name of item type to retrieve, e.g. "pr" or "issue"
        :type item_type: str
        :param cur_item: the current API item to get data about, e.g. current PR
        :type cur_item: PyGitHub PR or Issue
        :return: dictionary of API data values for param item
        :rtype: dict
        """
        field_list = self.get_cfg_val(f"{item_type}_fields")

        cmd_tbl = schema.cmd_tbl_dict[item_type]

        # when called, this will resolve to various function calls, e.g.
        # "body": cmd_tbl["body"](cur_PR)
        return {field: cmd_tbl[field](cur_item) for field in field_list}

    def __get_paged_list(self, key):
        return self.paged_list_dict[key]

    def __get_paged_list_dict(self):
        """
        retrieves and stores a paginated list from GitHub

        :param list_type str: type of paginated list to retrieve

        :raises github.RateLimitExceededException: if rate limited by the
        GitHub REST API, sleep the program until calls can be made again and
        continue attempt to collect desired paginated list

        :rtype None: sets object member to paginated list object
        """
        job_repo = self.get_cfg_val("repo")
        item_state = self.get_cfg_val("state")

        # create tuple of valid repo object function refs that get paginated
        # lists
        paged_ls_fn_ref_strs = {"issue": "get_issues", "pr": "get_pulls"}

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

                # create dict of {list type name: fn ref to get list}
                # e.g. {"issue": repo_obj.get_issues}
                paged_list_dict = {
                    ls_name: getattr(repo_obj, fn_name_str)(
                        direction="asc", sort="created", state=item_state
                    )
                    for ls_name, fn_name_str in paged_ls_fn_ref_strs.items()
                }

            except github.RateLimitExceededException:
                self.gh_sesh.sleep_gh_session()

            else:
                return paged_list_dict

    def get_pr_data(self) -> None:
        """
        retrieves both PR and commit data from the GitHub API; uses the "range"
        configuration value to determine what indices of the PR paged list to
        look at and the "pr_fields" and "commit_fields" configurationfields to
        determine what information it should retrieve from each PR of interest.

        commits are included by default because the commit info we are
        interested in descends from and is retrievable via PRs, i.e. we are
        not intereseted in commits that
            1. are not from an open or a closed and merged PR
            2. have no files changed by the commit

        :raises github.RateLimitExceededException: if rate limited by the
        GitHub REST API, dump collected data to output file and sleep the
        program until calls can be made again

        :rtype None
        """

        def __get_last_commit(pr_obj):
            """
            gets the paginated list of commits from a given pr, then returns the very
            last commit in that list of commits

            :param pr_obj Github.PullRequest: pr to source commit info from

            :rtype Github.Commit: last commit in the list of commits for current PR
            """
            # get paginated list of commits for PR at current index
            cur_commit_list = pr_obj.get_commits()

            # get index of commit we want from len of paginated list of commits
            last_commit_index = cur_commit_list.totalCount - 1

            # use that index to get the commit we are interested in
            return cur_commit_list[last_commit_index]

        data_type = "pr"
        data_dict = {data_type: {}}
        out_file = self.get_cfg_val("output_file")
        paged_list = self.__get_paged_list(data_type)

        # get indices of sanitized range values
        range_list = self._get_range_api_indices(paged_list)

        # unpack vals
        start_val = range_list[0]
        end_val = range_list[1]

        print(
            f"{' ' * 4}Beginning pull request/commit extraction. Starting may take a moment...\n"
        )

        while start_val < end_val + 1:
            try:
                # get current PR to begin information gathering
                cur_pr = paged_list[start_val]

                is_merged = cur_pr.merged

                # create dict to build upon. This variable will later become
                # the val of a dict entry, making it a subdictionary
                cur_entry = {"__pr_merged": is_merged}

                # if the current PR number is greater than or equal to the
                # first number provided in the "range" cfg val and the PR is
                # merged
                if is_merged or self.get_cfg_val("state") == "open":
                    cur_item_data = self.__get_item_data(data_type, cur_pr)

                    cur_entry = _merge_dicts(cur_entry, cur_item_data)

                    last_commit = __get_last_commit(cur_pr)

                    # if there are files changed for this commit
                    if len(last_commit.files) > 0:

                        # get all data from that commit
                        cur_item_data = self.__get_item_data(
                            "commit",
                            last_commit,
                        )

                        cur_entry = _merge_dicts(cur_entry, cur_item_data)

                # use all gathered entry data as the val for the PR num key
                cur_entry = {str(cur_pr.number): cur_entry}

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(data_dict, out_file)

            else:
                data_dict[data_type] = _merge_dicts(data_dict[data_type], cur_entry)
                self.gh_sesh.print_rem_gh_calls()

                start_val += 1

        file_io.write_merged_dict_to_json(data_dict, out_file)

    def __update_output_json_for_sleep(self, data_dict, out_file):
        """
        During rate limiting, we can update the JSON dict in the output file
        with the data that we have collected since we were last rate limited.
        This entails writing the current dict of data to the output file,
        clearing the current dictionary, and sleeping.

        :param data_dict: dictionary of current data to write to output file
        :type data_dict: dict
        :param out_file: path to output file
        :type out_file: string
        """
        file_io.write_merged_dict_to_json(data_dict, out_file)
        data_dict.clear()
        self.gh_sesh.sleep_gh_session()

        return data_dict
