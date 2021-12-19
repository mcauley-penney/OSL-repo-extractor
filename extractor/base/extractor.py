"""
The extractor module provides and exposes functionality to mine GitHub repositories.
"""

import json
from json.decoder import JSONDecodeError
import logging
import os
import github
from base import conf, sessions

PAGE_LEN = 35
TIME_FMT = "%D, %I:%M:%S %p"


def _get_api_item_indices(paged_list, range_list) -> list[int]:
    """
    sanitize our range values so that they are guaranteed to be safe, find the indices
    of those values inside of the paginated list, and return

    :param paged_list Github.PaginatedList of Github.Issues or Github.PullRequests:
    list of API objects

    :param range_list list[int]: list of range beginning and end values that we wish to
    find in the given paginated list

    :rtype int: list of indices to the paginated list of items that we wish to find
    """

    def __bin_search(paged_list_page, val) -> int:
        """
        Iterative binary search modified to return either the exact index of the item
        with the number the user desires or the index of the item beneath that value in
        the case that the value does not exist in the list. An example might be that a
        paginated list of issues does not have #'s 9, 10, or 11, but the user wants to
        begin looking for data at #10. This binary search should return the index of the
        API object with the number 8.

        :param paged_list_page Github.PaginatedList of Github.Issues or
        Github.PullRequests: list of API objects

        :param val int: the value that we wish to find the index of, e.g. the index of
        PR #10

        :rtype int: index of the object we are looking for
        """

        low = 0
        high = PAGE_LEN

        # because this binary search is looking through lists that may have items
        # missing, we want to be able to return the index of the nearest item before the
        # item we are looking for. Therefore, we stop when low is one less than high.
        # This allows us to take the lower value when a value does not exist in the
        # list.
        while low < high - 1:
            mid = (low + high) // 2

            cur_val = paged_list_page[mid].number

            if val == cur_val:
                return mid

            if val < cur_val:
                high = mid - 1

            elif val > cur_val:
                low = mid + 1

        return low

    def __get_last_item_num(paged_list) -> int:
        """
        Finds the number, e.g. issue number, of the last item in a given
        paginated list

        Simply slicing is INCREDIBLY slow, e.g.
            last_index = paged_list.totalCount - 1
            last_item_num = paged_list[last_index].number

        :param paged_list Github.PaginatedList of Github.Issues or Github.PullRequests:
        list of API objects

        :rtype int: the number of the last item in the paginated list
        """
        # get the total amount of items in the list
        last_index = paged_list.totalCount - 1

        # divide that value by the quantity of items per page to find the last page
        last_page = last_index // PAGE_LEN

        # get the last item from the last page
        last_item = paged_list.get_page(last_page)[-1]

        # return its number
        return last_item.number

    page_index = 0
    out_list = []

    print(f"{' ' * 4}Sanitizing range configuration values...")

    # get the highest item num in the paginated list of items, e.g. PR #8339 for
    # JabRef
    highest_num = __get_last_item_num(paged_list)

    # get sanitized range. This will correct any vals given in the range cfg so that
    # they are within the values that are in the paged list
    sani_range_tuple = (min(val, highest_num) for val in (range_list[0], range_list[1]))

    print(f"{' ' * 4}finding starting and ending indices of range values...\n")

    # for the two boundaries in the sanitized range
    for val in sani_range_tuple:

        # while the last item on the page is less than the val we are looking for, go to
        # the next page. When this fails, we know that the value we are looking for is
        # on the page we are on. This will yield the correct page to search in the
        # binary search in the next step
        while paged_list.get_page(page_index)[-1].number < val:
            page_index += 1

        # use iterative binary search to find item in correct page of linked list
        item_index = __bin_search(paged_list.get_page(page_index), val)

        # the index of the item we need is the amount of items per page that were
        # skipped plus the index of the item in it's page
        out_list.append((page_index * PAGE_LEN) + item_index)

    return out_list


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


def _get_num(api_obj) -> str:
    """
    Casts PR/Issue num received from GitHub API to a str and returns it

    The Python JSON module will cast all items to str. If we want to use the
    PR/issue num as a key inside of our JSON/output dicts, we must also cast to
    str. This will allow our JSON writing methods to recognize that the key of data
    that has already been written to JSON (and is thus a str) is the same as the
    key written during our latest round of API calls. For example, if we have
    Issue #1 in our JSON output already, the key (#1) has been casted to a str.
    In a hypothetical situation, we want to update #1 to have more info. If we get
    that new info for #1 in a round of API calls and attempt to update #1 in the
    already-existing JSON (which would happen in concat_json()) without casting
    this val to a str, the function will not recognize that the two keys are the
    same and will yield N separate entries for the same key, where N is the amount
    of times data is retrieved for that key

    :param api_obj github.PullRequest/github.Issue: PR or Issue to get num of
    """
    return str(api_obj.number)


def _get_pr_merged(pr_obj) -> bool:
    return pr_obj.merged


def _get_title(api_obj) -> str:
    return api_obj.title


def _get_username(api_obj) -> str:
    return _clean_str(api_obj.user.name)


def _get_userlogin(api_obj) -> str:
    return _clean_str(api_obj.user.login)


def _get_commit_auth_date(api_obj) -> str:
    return api_obj.commit.author.date.strftime(TIME_FMT)


def _get_commit_auth_name(api_obj) -> str:
    return api_obj.commit.author.name


def _get_commit_committer(api_obj) -> str:
    return api_obj.commit.committer.name


def _get_commit_files(api_obj) -> dict[str, int | str | list]:
    """
    For the list of files modified by a commit on a PR, return a list of qualities

    :param api_obj PaginatedList: paginated list of commits

    NOTE: If a list of files is too large, it will be returned as a paginatied
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


class Extractor:
    """
    The Extractor class contains and executes GitHub REST API functionality. It
    initiates and holds onto an object that stores the configuration for the program
    execution, an object that initiates and contains a connection to the GitHub API, and
    an object that writes content to JSON files.
    """

    # init dispatch tables that allow us to use strings to access functions
    # intro: https://betterprogramming.pub/dispatch-tables-in-python-d37bcc443b0b
    __COMMIT_CMD_DISPATCH = {
        "commit_author_name": _get_commit_auth_name,
        "committer": _get_commit_committer,
        "commit_date": _get_commit_auth_date,
        "commit_files": _get_commit_files,
        "commit_message": _get_commit_msg,
        "commit_sha": _get_commit_sha,
    }

    __ISSUE_CMD_DISPATCH = {
        "issue_body": _get_body,
        "issue_closed": _get_closed_time,
        "issue_comments": _get_issue_comments,
        "__issue_num": _get_num,
        "issue_title": _get_title,
        "issue_userlogin": _get_userlogin,
        "issue_username": _get_username,
    }

    __PR_CMD_DISPATCH = {
        "pr_body": _get_body,
        "pr_closed": _get_closed_time,
        "__pr_num": _get_num,
        "pr_merged": _get_pr_merged,
        "pr_title": _get_title,
        "pr_userlogin": _get_userlogin,
        "pr_username": _get_username,
    }

    # see cerberus documentation for schema rules
    # https://docs.python-cerberus.org/en/stable/index.html
    #
    # Above you can see a large amount of private getter methods that interact with
    # GitHub API objects and a few dictionaries that point to these methods. They have
    # been placed there because this position allows them to be referenced in this
    # schema. This cerberus schema defines what is and is not acceptable as inputs to
    # the program, specifically to the configuration object. We want to define this
    # AFTER we have defined our dispatch tables (the dictionaries above) because the
    # dictionary keys can then be used to define what fields are acceptable in the
    # "fields" schema fields. As you can see below, we unpack the dictionary keys into
    # a list ('*' is the unpack operator. Unpacking a dictionary retrieves the keys and
    # the square brackets contains the keys in a list) and that list acts as the
    # definition of what is acceptable in that field in the incoming configuration
    # JSON. This means that all you have to do to teach the configuration what is
    # acceptable in those fields is to add or remove the keys in the dicts above. For
    # example, if you decide that you want to allow the user to get a new item from PR
    # objects, such as the date the PR was made, you can just add a key to the dict and
    # the configuration will then know that it is allowed. This makes adding the ability
    # to get new information from the API expedient
    #
    # As an aside, Placing the private getter methods above the dict definitions allow
    # them to be used in the dict as vals
    CFG_SCHEMA = {
        "repo": {"type": "string"},
        "auth_file": {"type": "string"},
        "range": {
            "min": [0, 0],
            "schema": {"type": "integer"},
            "type": "list",
        },
        "commit_fields": {
            "allowed": [*__COMMIT_CMD_DISPATCH],
            "schema": {"type": "string"},
            "type": "list",
        },
        "issues_fields": {
            "allowed": [*__ISSUE_CMD_DISPATCH],
            "schema": {"type": "string"},
            "type": "list",
        },
        "pr_fields": {
            "allowed": [*__PR_CMD_DISPATCH],
            "schema": {"type": "string"},
            "type": "list",
        },
        "output_dir": {"type": "string"},
    }

    def __init__(self, cfg_path) -> None:
        """
        Initialize an extractor object. This object is our top-level actor and must be
        used by the user to extract data, such as in a driver program
        """

        self.__logger = logging.getLogger(__name__)

        self.__logger.info("Beginning extractor init, instantiating cfg...\n")

        # initialize configuration object
        self.cfg = conf.Cfg(cfg_path, self.CFG_SCHEMA)

        auth_path = self.cfg.get_cfg_val("auth_file")
        out_dir = self.cfg.get_cfg_val("output_dir")
        repo = self.cfg.get_cfg_val("repo")

        # initialize authenticated GitHub session
        self.gh_sesh = sessions.GithubSession(auth_path, PAGE_LEN)

        # initialize writer object
        self.writer = Writer(out_dir, repo)

        self.pr_paged_list = self.__get_paged_list("pr")
        self.issues_paged_list = self.__get_paged_list("issues")

    def get_issues_data(self) -> None:
        """
        Retrieves issue data from the GitHub API; uses the "range" configuration value
        to determine what indices of the issue paged list to look at and the
        "issues_fields" field to determine what information it should retrieve from
        each issues of interest

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, dump collected data to output file and sleep the program until calls can be
        made again
        """

        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        # get indices of sanitized range values
        range_list = _get_api_item_indices(self.issues_paged_list, val_range)

        # unpack vals
        start_val = range_list[0]
        end_val = range_list[1]

        while start_val < end_val:
            try:
                cur_issue = self.issues_paged_list[start_val]
                cur_issue_num = self.__ISSUE_CMD_DISPATCH["__issue_num"](cur_issue)

                cur_item_data = {
                    field: self.__ISSUE_CMD_DISPATCH[field](cur_issue)
                    for field in self.cfg.get_cfg_val("issues_fields")
                }

                cur_entry = {cur_issue_num: cur_item_data}

            except github.RateLimitExceededException:
                self.writer.concat_json(data_dict)
                data_dict.clear()
                self.gh_sesh.sleep()

            else:
                data_dict |= cur_entry
                self.gh_sesh.print_rem_calls()

                start_val = start_val + 1

        self.writer.concat_json(data_dict)

    def __get_paged_list(self, list_type):
        """
        retrieve and store a paginated list from GitHub

        :param list_type str: type of paginated list to retrieve

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, sleep the program until calls can be made again and continue attempt to
        collect desired paginated list

        :rtype None: sets object member to paginated list object
        """
        job_repo = self.cfg.get_cfg_val("repo")

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

                if list_type == "issues":
                    return repo_obj.get_issues(
                        direction="asc", sort="created", state="closed"
                    )

                return repo_obj.get_pulls(
                    direction="asc", sort="created", state="closed"
                )

            except github.RateLimitExceededException:
                self.gh_sesh.sleep()

    def get_pr_data(self) -> None:
        """
        Retrieves both PR and commit data from the GitHub API; uses the "range"
        configuration value to determine what indices of the PR paged list to
        look at and the "pr_fields" and "commit_fields" configurationfields to
        determine what information it should retrieve from each PR of interest.

        Commits are included by default because the commit info we are interested in
        descends from and is retrievable via PRs, i.e. we are not intereseted in
        commits that
            1. are not from a closed and merged PR
            2. have no files changed by the commit

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, dump collected data to output file and sleep the program until calls can
        be made again

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

        data_dict = {}

        # get fields of values desired from API
        commit_fields = self.cfg.get_cfg_val("commit_fields")
        pr_fields = self.cfg.get_cfg_val("pr_fields")

        # get range cfg value
        val_range = self.cfg.get_cfg_val("range")

        # get indices of sanitized range values
        range_list = _get_api_item_indices(self.pr_paged_list, val_range)

        # unpack vals
        start_val = range_list[0]
        end_val = range_list[1]

        while start_val < end_val:
            try:
                # get current PR to begin information gathering
                cur_pr = self.pr_paged_list[start_val]

                is_merged = cur_pr.merged

                # create dict to build upon. This variable will later become the val of
                # a dict entry, making it a subdictionary
                cur_entry = {"pr_merged": is_merged}

                # if the current PR number is greater than or equal to the first
                # number provided in the "range" cfg val and the PR is merged
                if is_merged:
                    cur_entry |= {
                        field: self.__PR_CMD_DISPATCH[field](cur_pr)
                        for field in pr_fields
                    }

                    last_commit = __get_last_commit(cur_pr)

                    # if there are files changed for this commit
                    if len(last_commit.files) > 0:

                        # get all data from that commit
                        cur_entry |= {
                            field: self.__COMMIT_CMD_DISPATCH[field](last_commit)
                            for field in commit_fields
                        }

                # get the current PR number as a string
                cur_pr_num = self.__PR_CMD_DISPATCH["__pr_num"](cur_pr)

                # use all gathered entry data as the val for the PR num key
                cur_entry = {cur_pr_num: cur_entry}

            except github.RateLimitExceededException:
                # concatenate gathered data, clear the dict, and sleep
                self.writer.concat_json(data_dict)
                data_dict.clear()
                self.gh_sesh.sleep()

            else:
                data_dict |= cur_entry
                self.gh_sesh.print_rem_calls()

                start_val += 1

        self.writer.concat_json(data_dict)


class Writer:
    """
    The Writer class creates objects that can be used to write data to output files
    """

    def __init__(self, output_dir, full_repo) -> None:
        """
        initialize Writer object

        :param output_dir str: path of output dir, from Cfg object

        :param full_repo str: name of the repo to extract from, e.g. "Owner/Repo"

        :rtype None: initializes Writer object
        """

        # lop repo str off of full repo info, e.g. owner/repo
        repo_name = full_repo.rsplit("/", 1)[1]

        # init output subdir for this repo and hold onto it
        repo_subdir = f"{output_dir}/{repo_name}"

        # create output directory only if it does not exist
        os.makedirs(repo_subdir, exist_ok=True)

        self.output_file = f"{repo_subdir}/{repo_name}_output.JSON"

        # for each file above, create it if it does not exist
        if not os.path.exists(self.output_file):
            os.mknod(self.output_file)

    def concat_json(self, out_dict) -> None:
        """
        gets the desired output path, opens and reads any JSON data that may already be
        there, and recursively merges in param data from the most recent round of API
        calls

        :param out_type str: the type of output being created, e.g. "commit", "issues"

        :param out_dict dict[unknown]: dict of data from round of API calls to merge and
        write

        :rtype None: writes output to file, nothing returned
        """

        def __merge_dicts(add_dict, base_dict) -> None:
            """
            loops through keys in dictionary of data from round of API calls to merge
            their data into existing JSON data

            :param add_dict dict[unknown]: dict of data to be written

            :param base_dict dict[unknown]: dict of data already written to and read out
            from JSON file

            :rtype None: merges param dicts

            :credit Paul Durivage: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
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
                    __merge_dicts(add_dict[key], base_dict[key])

                else:
                    # assign the new value from the last round of calls to the existing
                    # key
                    base_dict[key] = add_dict[key]

        json_dict = {}

        path = self.output_file

        # attempt to read JSON out of output file
        try:
            with open(self.output_file, "r", encoding="UTF-8") as json_outfile:
                json_dict = json.load(json_outfile)

        # if no JSON content exists there, ignore
        except JSONDecodeError:
            pass

        # in any case
        finally:
            # recursively merge all dicts and nested dicts in both dictionaries
            __merge_dicts(out_dict, json_dict)

            # write JSON content back to file
            with open(path, "w", encoding="UTF-8") as json_outfile:
                json.dump(json_dict, json_outfile, ensure_ascii=False, indent=4)
