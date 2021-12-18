"""
The extractor module provides and exposes functionality to mine GitHub repositories.
"""

import json
from json.decoder import JSONDecodeError
import logging
import os
import github
from base import conf, sessions


TIME_FMT = "%D, %I:%M:%S %p"


class Extractor:
    """
    The Extractor class contains and executes GitHub REST API functionality. It
    initiates and holds onto an object that stores the configuration for the program
    execution, an object that initiates and contains a connection to the GitHub API, and
    an object that writes content to JSON files.
    """

    def __clean_str(self, str_to_clean):
        """
        If a string is empty or None, returns NaN. Otherwise, strip the string of any
        carriage returns, newlines, and leading or trailing whitespace.

        :param str_to_clean str: string to clean and return
        """
        if str_to_clean is None or str_to_clean == "":
            output_str = "Nan"

        else:
            output_str = str_to_clean.replace("\r", "")
            output_str = output_str.replace("\n", "")

        return output_str.strip()

    def __get_body(self, api_obj):
        """
        return issue or PR text body

        :param api_obj github.PullRequest/github.Issue: API object to get body text of
        """
        return self.__clean_str(api_obj.body)

    def __get_closed_time(self, api_obj):
        """
        if the API object has been closed, i.e. closed PR or issue, return the formatted
        datetime that it was closed at

        :param api_obj github.PullRequest/github.Issue: API object to get datetime of
        closing of
        """
        if api_obj.closed_at is not None:
            return api_obj.closed_at.strftime(TIME_FMT)

        return "NaN"

    def __get_issue_comments(self, issue_obj):
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
            return self.__clean_str(comment_str)

        return "NaN"

    def __get_num(self, api_obj):
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

    def __get_pr_merged(self, pr_obj):
        return pr_obj.merged

    def __get_title(self, api_obj):
        return api_obj.title

    def __get_username(self, api_obj):
        return self.__clean_str(api_obj.user.name)

    def __get_userlogin(self, api_obj):
        return self.__clean_str(api_obj.user.login)

    def __get_commit_auth_date(self, api_obj):
        return api_obj.commit.author.date.strftime(TIME_FMT)

    def __get_commit_auth_name(self, api_obj):
        return api_obj.commit.author.name

    def __get_commit_committer(self, api_obj):
        return api_obj.commit.committer.name

    def __get_commit_files(self, api_obj):
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
            "patch_text": self.__clean_str(commit_patch_text),
            "removals": commit_removes,
            "status": self.__clean_str(quoted_commit_status_str),
        }

    def __get_commit_msg(self, api_obj):
        return self.__clean_str(api_obj.commit.message)

    def __get_commit_sha(self, api_obj):
        return api_obj.sha

    # init dispatch tables that allow us to use strings to access functions
    # intro: https://betterprogramming.pub/dispatch-tables-in-python-d37bcc443b0b
    COMMIT_CMD_DISPATCH = {
        "commit_author_name": __get_commit_auth_name,
        "committer": __get_commit_committer,
        "commit_date": __get_commit_auth_date,
        "commit_files": __get_commit_files,
        "commit_message": __get_commit_msg,
        "commit_sha": __get_commit_sha,
    }

    ISSUE_CMD_DISPATCH = {
        "issue_body": __get_body,
        "issue_closed": __get_closed_time,
        "issue_comments": __get_issue_comments,
        "__issue_num": __get_num,
        "issue_title": __get_title,
        "issue_userlogin": __get_userlogin,
        "issue_username": __get_username,
    }

    PR_CMD_DISPATCH = {
        "pr_body": __get_body,
        "pr_closed": __get_closed_time,
        "__pr_num": __get_num,
        "pr_merged": __get_pr_merged,
        "pr_title": __get_title,
        "pr_userlogin": __get_userlogin,
        "pr_username": __get_username,
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
            "allowed": [*COMMIT_CMD_DISPATCH],
            "schema": {"type": "string"},
            "type": "list",
        },
        "issues_fields": {
            "allowed": [*ISSUE_CMD_DISPATCH],
            "schema": {"type": "string"},
            "type": "list",
        },
        "pr_fields": {
            "allowed": [*PR_CMD_DISPATCH],
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

        # initialize authenticated GitHub session
        self.gh_sesh = sessions.GithubSession(self.cfg.get_cfg_val("auth_file"))

        # initialize writer object
        self.writer = Writer(
            self.cfg.get_cfg_val("output_dir"), self.cfg.get_cfg_val("repo")
        )

        self.pr_paged_list = self.get_paged_list("pr")
        self.issues_paged_list = self.get_paged_list("issues")

    def __sanitize_range_val(self, paged_list, val_to_check) -> int:
        """
        Compares the given values in the "range" cfg field and lowers them if they are
        larger than the largest item number present at the end of the paged list param

        :param paged_list Github.PaginatedList of Github.Issues or Github.PullRequests:
        list of API objects
        :param val_to_check int: value in range cfg to check against paginated list
        :rtype int: sanitized value; lower than the maximimum item number in the
        paginated list
        """

        def __get_last_item_num() -> int:
            """
            Finds the number, e.g. issue number, of the last item in a given
            paginated list

            Simply slicing is INCREDIBLY slow, e.g.
                last_index = paged_list.totalCount - 1
                last_item_num = paged_list[last_index].number

            :rtype int: the number of the last item in the paginated list
            """
            # get the total amount of items in the list
            last_index = paged_list.totalCount - 1

            # divide that value by the quantity of items per page to find the last page
            last_page = last_index // 30

            # get the number of the last item from the last page
            return paged_list.get_page(last_page)[-1].number

        last_item_num = __get_last_item_num()

        if val_to_check > last_item_num:
            return last_item_num

        return val_to_check

    def get_issues_data(self):
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
        paged_list = self.issues_paged_list

        cmd_dict = self.ISSUE_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("issues_fields")

        # adjust amount of rows to get if unsafe
        safe_start_val = self.__sanitize_range_val(paged_list, val_range[0])
        safe_end_val = self.__sanitize_range_val(paged_list, val_range[1])

        while safe_start_val < safe_end_val:
            try:
                cur_issue = paged_list[safe_start_val]
                cur_issue_num = self.ISSUE_CMD_DISPATCH["__issue_num"](self, cur_issue)
                cur_entry = {}

                if int(cur_issue_num) >= safe_start_val:
                    cur_item_data = {
                        field: cmd_dict[field](self, cur_issue) for field in field_list
                    }

                    cur_entry = {cur_issue_num: cur_item_data}

            except github.RateLimitExceededException:
                self.writer.concat_json(data_dict)
                data_dict = {}
                self.gh_sesh.sleep()

            else:
                data_dict.update(cur_entry)
                self.gh_sesh.print_rem_calls()

                safe_start_val = safe_start_val + 1

        self.writer.concat_json(data_dict)

    def get_paged_list(self, list_type):
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

                else:
                    return repo_obj.get_pulls(
                        direction="asc", sort="created", state="closed"
                    )

            except github.RateLimitExceededException:
                self.gh_sesh.sleep()

    def get_pr_data(self, get_commits=True):
        """
        By default, retrieves both PR and commit data from the GitHub API; uses the
        "range" configuration value to determine what indices of the PR paged list to
        look at and the "pr_fields" and "commit_fields" configurationfields to
        determine what information it should retrieve from each PR of interest.

        Commits are included by default because the commit info we are interested in
        descends from and is retrievable via PRs, i.e. we are not intereseted in
        commits that
            1. are not from a closed and merged PR
            2. has no files changed by the commit

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
        index = 0
        val_range = self.cfg.get_cfg_val("range")
        pr_list = self.pr_paged_list

        pr_dict = self.PR_CMD_DISPATCH
        pr_fields = self.cfg.get_cfg_val("pr_fields")

        commit_dict = self.COMMIT_CMD_DISPATCH
        commit_fields = self.cfg.get_cfg_val("commit_fields")

        # lower any errant rows down to max value
        safe_start_val = self.__sanitize_range_val(pr_list, val_range[0])
        safe_end_val = self.__sanitize_range_val(pr_list, val_range[1])

        while index < safe_end_val:
            try:
                # get current PR to begin information gathering
                cur_pr = pr_list[index]

                # get the current PR number as a string
                cur_pr_num = self.PR_CMD_DISPATCH["__pr_num"](self, cur_pr)

                # determine whether the current pr is merged so that we can decide if we
                # want the rest of its data
                is_merged = cur_pr.merged

                cur_entry = {cur_pr_num: {"pr_merged": is_merged}}

                # if the current PR number is greater than or equal to the first
                # number provided in the "range" cfg val and the PR is merged
                if is_merged and int(cur_pr_num) >= safe_start_val:
                    cur_item_pr_data = {
                        field: pr_dict[field](self, cur_pr) for field in pr_fields
                    }

                    if get_commits:
                        last_commit = __get_last_commit(cur_pr)

                        # if there are files changed for this commit
                        if len(last_commit.files) > 0:

                            # get all data from that commit
                            cur_item_commit_data = {
                                field: commit_dict[field](self, last_commit)
                                for field in commit_fields
                            }

                            # merge the current PR data and the current commit data
                            # into one dictionary
                            cur_item_pr_data |= cur_item_commit_data

                    # create dict entry using the issue num associated with the commit
                    # as the key
                    cur_entry = {cur_pr_num: cur_item_pr_data}

            except github.RateLimitExceededException:
                self.writer.concat_json(data_dict)
                data_dict = {}
                self.gh_sesh.sleep()

            else:
                data_dict.update(cur_entry)
                self.gh_sesh.print_rem_calls()

                index += 1

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

        # self.commit_output = f"{repo_subdir}/commit_output.JSON"
        # self.issues_output = f"{repo_subdir}/commit_output.JSON"
        self.output_file = f"{repo_subdir}/{repo_name}_output.JSON"

        # for each file above, create it if it does not exist
        if not os.path.exists(self.output_file):
            os.mknod(self.output_file)

    def concat_json(self, out_dict):
        """
        gets the desired output path, opens and reads any JSON data that may already be
        there, and recursively merges in param data from the most recent round of API
        calls

        :param out_type str: the type of output being created, e.g. "commit", "issues"

        :param out_dict dict[unknown]: dict of data from round of API calls to merge and
        write

        :rtype None: writes output to file, nothing returned
        """

        def __merge_dicts(add_dict, base_dict):
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
            with open(self.output_file, "r") as json_outfile:
                json_dict = json.load(json_outfile)

        # if no JSON content exists there, ignore
        except JSONDecodeError:
            pass

        # in any case
        finally:
            # recursively merge all dicts and nested dicts in both dictionaries
            __merge_dicts(out_dict, json_dict)

            # write JSON content back to file
            with open(path, "w") as json_outfile:
                json.dump(json_dict, json_outfile, ensure_ascii=False, indent=4)
