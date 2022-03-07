"""
This module is a monolothic compilation of the source code for the extractor.
The intention is to provide a means of running the extractor without having to
modify the user's PYTHONPATH env var.
"""

import argparse
import json
from json.decoder import JSONDecodeError
import os
import sys
import time
import cerberus
import github

TIME_FMT = "%D, %I:%M:%S %p"


def main():
    """driver function for GitHub Extractor"""

    cfg_path = get_cli_args()

    # init extractor object
    print("\nBeginning extractor init, instantiating cfg...")
    gh_ext = Extractor(cfg_path)

    if gh_ext.get_cfg_val("issue_fields"):
        print("\nGetting issue data...")
        gh_ext.get_issues_data()
        print("\nIssue data complete!")

    else:
        print("\nNo issue fields given! Proceeding...")

    if gh_ext.get_cfg_val("pr_fields"):
        print("\nGetting pull request data...")
        gh_ext.get_pr_data()
        print("\nPull request data complete!")

    else:
        print("\nNo pull request fields given!")

    print("\nExtraction complete!")


def get_cli_args() -> str:
    """
    get initializing arguments from CLI

    :rtype str: path to file with arguments to program
    """

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Gathers and stores specific data from GitHub repositories",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_cfg_file",
        help="Path to configuration file for the extractor",
    )

    return arg_parser.parse_args().extractor_cfg_file


def _clean_str(str_to_clean) -> str:
    """
    If a string is empty or None, returns NaN. Otherwise, strip the string of any
    carriage returns, newlines, and leading or trailing whitespace.

    :param str_to_clean str: string to clean and return
    """
    if str_to_clean is None or str_to_clean == "":
        return "Nan"

    output_str = str_to_clean.replace("\r", "")
    output_str = output_str.replace("\n", "")

    return output_str.strip()


def _get_body(api_obj) -> str:
    """
    return issue or PR text body

    :param api_obj github.PullRequest/github.Issue: API object to get body text of
    """
    return _clean_str(api_obj.body)


def _get_closed_time(api_obj) -> str:
    """
    if the API object has been closed, i.e. closed PR or issue, return the formatted
    datetime that it was closed at

    :param api_obj github.PullRequest/github.Issue: API object to get datetime of
    closing of
    """
    if api_obj.closed_at is not None:
        return api_obj.closed_at.strftime(TIME_FMT)

    return "NaN"


def _get_issue_comments(issue_obj) -> str:
    """
    if a given issue has comments, collect them all into one string separated by a
    special delimeter, format the str, and return it

    :param api_obj github.Issue: Issue object to comments of
    """
    comments_paged_list = issue_obj.get_comments()

    if comments_paged_list.totalCount != 0:
        sep_str = " =||= "

        # get body from each comment, strip of whitespace, and join w/ special char
        comment_str = sep_str.join(
            comment.body.strip() for comment in comments_paged_list
        )

        # strip comment string of \n, \r, and whitespace again
        return _clean_str(comment_str)

    return "NaN"


def _get_pr_merged(pr_obj) -> bool:
    return pr_obj.merged


def _get_title(api_obj) -> str:
    return api_obj.title


def _get_username(api_obj) -> str:
    return _clean_str(api_obj.user.name)


def _get_userlogin(api_obj) -> str:
    return _clean_str(api_obj.user.login)


def _get_commit_date(api_obj) -> str:
    return api_obj.commit.author.date.strftime(TIME_FMT)


def _get_commit_author_name(api_obj) -> str:
    return api_obj.commit.author.name


def _get_commit_committer(api_obj) -> str:
    return api_obj.commit.committer.name


def _get_commit_files(api_obj) -> dict:
    """
    For the list of files modified by a commit on a PR, return a list of qualities

    :param api_obj PaginatedList: paginated list of commits

    NOTE:
        If a list of files is too large, it will be returned as a paginatied
        list. See note about the list length constraints at
        https://docs.github.com/en/rest/reference/commits#get-a-commit. As of right
        now, this situation is not handled here.

    :rtype dict[unknown]: dictionary of fields discussing file attributes of a
    commit
    """
    file_list = api_obj.files

    commit_file_list = []
    commit_adds = 0
    commit_changes = 0
    commit_patch_text = ""
    commit_removes = 0
    commit_status_str = ""

    for file in file_list:
        commit_file_list.append(file.filename)
        commit_adds += int(file.additions)
        commit_changes += int(file.changes)
        commit_patch_text += str(file.patch) + ", "
        commit_removes += int(file.deletions)
        commit_status_str += str(file.status) + ", "

    quoted_commit_status_str = '"' + commit_status_str + '"'

    return {
        "file_list": commit_file_list,
        "additions": commit_adds,
        "changes": commit_changes,
        "patch_text": _clean_str(commit_patch_text),
        "removals": commit_removes,
        "status": _clean_str(quoted_commit_status_str),
    }


def _get_commit_msg(api_obj) -> str:
    return _clean_str(api_obj.commit.message)


def _get_commit_sha(api_obj) -> str:
    return api_obj.sha


cmd_tbl_dict = {
    "commit": {
        "commit_author_name": _get_commit_author_name,
        "committer": _get_commit_committer,
        "commit_date": _get_commit_date,
        "commit_files": _get_commit_files,
        "commit_message": _get_commit_msg,
        "commit_sha": _get_commit_sha,
    },
    "issue": {
        "body": _get_body,
        "closed": _get_closed_time,
        "issue_comments": _get_issue_comments,
        "title": _get_title,
        "userlogin": _get_userlogin,
        "username": _get_username,
    },
    "pr": {
        "body": _get_body,
        "closed": _get_closed_time,
        "__pr_merged": _get_pr_merged,
        "title": _get_title,
        "userlogin": _get_userlogin,
        "username": _get_username,
    },
}


cfg_schema = {
    "repo": {"type": "string"},
    "auth_file": {"type": "string"},
    "state": {"allowed": ["closed", "open"], "type": "string"},
    "range": {"min": [0, 0], "schema": {"type": "integer"}, "type": "list"},
    "commit_fields": {
        "allowed": [*cmd_tbl_dict["commit"]],
        "schema": {"type": "string"},
        "type": "list",
    },
    "issue_fields": {
        "allowed": [*cmd_tbl_dict["issue"]],
        "schema": {"type": "string"},
        "type": "list",
    },
    "pr_fields": {
        "allowed": [*cmd_tbl_dict["pr"]],
        "schema": {"type": "string"},
        "type": "list",
    },
    "output_dir": {"type": "string"},
}


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
        cfg_dict = read_json_to_dict(cfg_path)

        # initialize configuration object with cfg dict
        self.cfg = Cfg(cfg_dict, cfg_schema)

        auth_path = self.get_cfg_val("auth_file")

        # initialize authenticated GitHub session
        self.gh_sesh = GithubSession(auth_path)

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

            # use iterative binary search to find item in correct page of linked list
            item_page_index = __bin_search_in_page(
                paged_list.get_page(page_index), page_len, val
            )

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

        print("Beginning issue extraction. Starting may take a moment...\n")

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

        write_merged_dict_to_json(data_dict, out_file)

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

        cmd_tbl = cmd_tbl_dict[item_type]

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
            "Beginning pull request/commit extraction. Starting may take a moment...\n"
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

        write_merged_dict_to_json(data_dict, out_file)

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
        write_merged_dict_to_json(data_dict, out_file)
        data_dict.clear()
        self.gh_sesh.sleep_gh_session()

        return data_dict


class Cfg:
    """
    The Cfg class provides an object which holds all of the configuration
    for the extractor class
    """

    def __init__(self, cfg_dict: dict, schema) -> None:
        """
        initialize an object to hold configuration values for the extractor

        :param cfg_file str: path name to a configuration file
        :rtype None: initializes Cfg obj
        """
        # hold onto dict from cfg JSON file
        self.cfg_dict = cfg_dict
        self.cfg_schema = schema

        # validate cfg dict
        self.__validate_dict_entries()

        # use repo and output dir from cfg to create path to write output to
        self.__set_full_output_dir()

    def get_cfg_val(self, key: str):
        """
        print the associated value of key param

        :param key str: associated key for desired val; defaults
        to returning the path to the config file
        """
        return self.cfg_dict[key]

    def set_cfg_val(self, key: str, val) -> None:
        """
        set a value inside of the configuration dict

        :param key str: the key of the dict entry to modify
        :param val str | int: value to assign to dict[key]
        :rtype None
        """
        self.cfg_dict[key] = val

    def __set_full_output_dir(self):
        """ """

        out_dir = self.get_cfg_val("output_dir")

        # lop repo str off of full repo info, e.g. owner/repo
        repo_name = self.get_cfg_val("repo").rsplit("/", 1)[1]

        # init output subdir for this repo and hold onto it
        repo_subdir = f"{out_dir}/{repo_name}"

        # create output directory only if it does not exist
        os.makedirs(repo_subdir, exist_ok=True)

        out_file = f"{repo_subdir}/{repo_name}_output.json"

        self.set_cfg_val("output_file", out_file)

        # for each file above, create it if it does not exist
        if not os.path.exists(out_file):
            os.mknod(out_file)

    def __validate_dict_entries(self) -> None:
        """
        use Cerberus to check all entries in the configuration dictionary for
        correctness of type and content

        See extractor.CFG_SCHEMA for what is permitted

        :rtype None: exits program with failure code if cfg dict is incorrect
        """

        # init schema for validation
        validator = cerberus.Validator(self.cfg_schema, require_all=True)

        # if dictionary from JSON does not follow rules in schema
        if not validator.validate(document=self.cfg_dict):
            # log an exception and print errors
            print(f"Validation error!\n {validator.errors}")
            sys.exit(1)


def _console_print_in_place(label_str: str, val) -> None:
    # clear line to erase any errors due to typing in the console
    print("", end="\r")

    # print output in place
    print(f"{' ' * 4}{label_str} {val}", end="\r")


class GithubSession:
    """
    The GithubSession class initializes and holds a verified connection to the GitHub
    API and exposes functionality for that connection up to the Extractor class
    """

    def __init__(self, auth_path) -> None:
        """
        initialize GitHub session object
        :param auth_path str: path to file containing personal access token
        """
        self.__page_len = 30
        self.session = self.__get_gh_session(auth_path)

    def __get_gh_session(self, auth_path) -> github.Github:
        """
        retrieves PAT from auth file, checks whether it is valid

        :raises github.BadCredentialsException: if given item is not a valid Personal
        Access Token

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, return the authorized session. If rate limited, it means that the given
        PAT is valid and a usable connection has been made

        :rtype None:
        """

        # retrieve token from auth file
        token = read_txt_line(auth_path)

        # establish a session with token
        session = github.Github(token, per_page=self.__page_len, retry=100, timeout=100)

        try:
            # if name can be gathered from token, properly authenticated
            session.get_user().name

        # if token is not valid, remove token from list
        except github.BadCredentialsException:
            # log that token is invalid
            print("Invalid personal access token found! Exiting...\n")
            sys.exit(1)

        # if rate limited at this stage, session must be valid
        except github.RateLimitExceededException:
            return session

        else:
            return session

    def get_pg_len(self):
        """
        getter method that allows access to page length of pages in GitHub API
        paginated lists
        """
        return self.__page_len

    def print_rem_gh_calls(self) -> None:
        """print remaining calls to API for this hour"""

        # get remaining calls before reset
        calls_left = self.session.rate_limiting[0]

        # format as a string
        calls_left_str = f"{calls_left:<4d}"

        _console_print_in_place("Calls left until sleep:", calls_left_str)

    def sleep_gh_session(self) -> None:
        """sleep the program until we can make calls again"""

        # time to wait is the amount of seconds until reset minus the current time
        countdown_time = self.session.rate_limiting_resettime - int(time.time())

        while countdown_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(countdown_time, 60)

            # format the time string before printing
            countdown_str = f"{minutes:02d}:{seconds:02d}"

            _console_print_in_place("time until limit reset:", countdown_str)

            # sleep for a while
            time.sleep(1)
            countdown_time -= 1


def read_json_to_dict(in_path: str) -> dict:
    """
    open the provided JSON file and read its contents out into a dictionary

    :raises FileNotFoundError: file does not exist at path
    :param cfg_file str: path name to a JSON configuration file
    :rtype dict: dictionary constructed from JSON string
    """

    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            json_text = file_obj.read()

    except FileNotFoundError:
        print(f"\nFile at {in_path} not found!")
        sys.exit(1)

    else:
        return json.loads(json_text)


def read_txt_line(in_path: str) -> str:
    """
    read a single line from the top of a text file.
    Used for reading personal access tokens (PATs) out of auth file

    :raises FileNotFoundError: file does not exist at path
    :param auth_file_path str: path to auth file
    :rtype pat_list list[str]: text lines from auth file
    """
    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            file_text = file_obj.readline()

    except FileNotFoundError:
        # if the file is not found log an error and exit
        print(f"\nFile at {in_path} not found!")
        sys.exit(1)

    else:
        return file_text.strip().strip("\n")


def write_dict_to_json(out_dict: dict, out_path: str) -> None:
    """
    write given Python dictionary to output file as JSON

    :raises FileNotFoundError: file does not exist at path
    :param out_dict dict: dictionary to write as JSON
    :param out_path str: path to write output to
    :rtype None
    """
    try:
        with open(out_path, "w", encoding="UTF-8") as json_outfile:
            json.dump(out_dict, json_outfile, ensure_ascii=False, indent=4)

    except FileNotFoundError:
        print(f"\nFile at {out_path} not found!")


def write_merged_dict_to_json(out_dict: dict, out_path: str) -> None:
    """
    gets the desired output path, opens and reads any JSON data that may already be
    there, and recursively merges in param data from the most recent round of API
    calls

    :param out_dict dict[unknown]: dict of data from round of API calls to merge and
    write
    :param out_path str: path to file in fs that we want to write to

    :rtype None: writes output to file, nothing returned
    """

    def __merge_dicts_recursive(add_dict, base_dict) -> None:
        """
        loops through keys in dictionary of data from round of API calls to merge
        their data into existing JSON data

        credit to Paul Durivage: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

        :param add_dict dict[unknown]: dict of data to be written

        :param base_dict dict[unknown]: dict of data already written to and read out
        from JSON file

        :rtype None: merges param dicts
        """
        # for each key in the dict that we created with the round of API calls
        for key in add_dict:

            # if that key is in the dict in the existing JSON file and the val at
            # the key is a dict in both dictionaries
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(add_dict[key], dict)
            ):
                # recurse
                __merge_dicts_recursive(add_dict[key], base_dict[key])

            else:
                # assign the new value from the last round of calls to the existing
                # key
                base_dict[key] = add_dict[key]

    json_dict = {}

    # attempt to read JSON out of output file
    try:
        json_dict = read_json_to_dict(out_path)

    # if no JSON content exists there, ignore. In this context, it simply means that we
    # are writing JSON to a new file
    except JSONDecodeError:
        pass

    # in any case
    finally:
        # recursively merge all dicts and nested dicts in both dictionaries
        __merge_dicts_recursive(out_dict, json_dict)

        # write JSON content back to file
        write_dict_to_json(json_dict, out_path)

    print()


if __name__ == "__main__":
    main()
