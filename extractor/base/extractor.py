"""
The extractor module provides and exposes functionality to mine GitHub repositories.

IMPORTANT: Take the time to read all long comments in this file before attempting to
modify it. These long comments are useful for understanding why things are written or
ordered the way that they are.
"""

import json
from json.decoder import JSONDecodeError
import logging
import os
import sys
import github
from base import conf, sessions


TIME_FMT = "%D, %I:%M:%S %p"


class Extractor:
    """
    # TODO:

    1. determine how we want to create or store output files. We should probably allow
    for separating the data and merging them later. concat_json can be used for that as
    well, so it should stay public.

    TODO: update
    The extractor class contains and executes GitHub REST API
    functionality. It holds onto a configuration object, initiates and
    holds onto the connection to GitHub, asks for information from GitHub and
    stores it in a dataset object, and has the ability to write that dataeset
    to JSON or a database.
    """

    def __clean_str(self, str_to_clean):
        """
        If a string is empty or None, returns NaN.
        Otherwise, strip the string of any carriage
        returns and newlines

        :param str_to_clean str: string to clean and return
        """

        if str_to_clean is None or str_to_clean == "":
            output_str = "Nan"

        else:
            output_str = str_to_clean.replace("\r", "")
            output_str = output_str.replace("\n", "")

        return output_str.strip()

    def __get_body(self, api_obj):
        return self.__clean_str(api_obj.body)

    def __get_closed_time(self, api_obj):
        if api_obj is not None:
            return api_obj.closed_at.strftime(TIME_FMT)

        return "NaN"

    def __get_issue_comments(self, issue_obj):

        comments_paged_list = issue_obj.get_comments()

        if comments_paged_list.totalCount != 0:
            # get body from each comment, strip of whitespace, and join w/ special char
            comment_str = " =||= ".join(
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
        "author_name": __get_commit_auth_name,
        "committer": __get_commit_committer,
        "date": __get_commit_auth_date,
        "files": __get_commit_files,
        "message": __get_commit_msg,
        "sha": __get_commit_sha,
    }

    ISSUE_CMD_DISPATCH = {
        "body": __get_body,
        "closed": __get_closed_time,
        "comments": __get_issue_comments,
        "num": __get_num,
        "title": __get_title,
        "userlogin": __get_userlogin,
        "username": __get_username,
    }

    PR_CMD_DISPATCH = {
        "body": __get_body,
        "closed": __get_closed_time,
        "num": __get_num,
        "merged": __get_pr_merged,
        "title": __get_title,
        "userlogin": __get_userlogin,
        "username": __get_username,
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

    def __check_row_quant_safety(self, paged_list, range_start, range_end) -> int:
        """
        validates second val of row range (end of data to collect) provided in cfg. If
        the second val in the range larger than the amount of items in the provided
        paginated list, corrects the second val to the length of the paginated list.

        :param paged_list Github.PaginatedList: paginated list containing items of
        interest

        :param range_end int: the last value that the user wants to look at; provided in
        the "range" field of the configuration

        :param range_start int: first val of the provided range
        :rtype int: returns the new end of the range
        """

        safe_val = range_end

        if range_end <= range_start or paged_list.totalCount < range_end:
            safe_val = paged_list.totalCount

        return safe_val

    def get_commit_data(self):
        """
        Retrieves commit data from the GitHub API; uses the "range" configuration value
        to determine what indices of the commit paged list to look at and the
        "commit_fields" field to determine what information it should retrieve from
        each issues of interest

        TODO: add ability to read from commit objects gotten and stored during PR data
        retrieval. This way is good because it is independent of PR data retrieval, but
        a choice would make it easier if we were getting everything anyway
        """

        def __get_last_commit(pr_obj):
            # get paginated list of commits for PR at current index
            cur_commit_list = pr_obj.get_commits()

            # get index of commit we want from len of paginated list of commits
            cur_commit_list_len = cur_commit_list.totalCount - 1

            # use that index to get the commit we are interested in
            return cur_commit_list[cur_commit_list_len]

        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        paged_list = self.pr_paged_list
        field_list = self.cfg.get_cfg_val("commit_fields")
        cmd_dict = self.COMMIT_CMD_DISPATCH

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = self.__check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                # reset
                cur_pr = paged_list[i]
                cur_pr_num = self.PR_CMD_DISPATCH["num"](self, cur_pr)
                cur_entry = {cur_pr_num: "Not Merged"}

                if cur_pr.merged:

                    last_commit = __get_last_commit(cur_pr)

                    # if there are files changed for this commit
                    if len(last_commit.files) > 0:

                        # get all data from that commit
                        cur_item_data = {
                            field: cmd_dict[field](self, last_commit)
                            for field in field_list
                        }

                        # create dict entry using the PR num associated with the commit
                        # as the key
                        cur_entry = {cur_pr_num: cur_item_data}

                        print(f"{cur_entry}\n")

            except github.RateLimitExceededException:
                self.writer.concat_json("commit", data_dict)
                data_dict = {}
                self.gh_sesh.sleep()

            else:
                data_dict.update(cur_entry)
                self.gh_sesh.print_rem_calls()

                i = i + 1

        # write what is left to JSON output file
        self.writer.concat_json("commit", data_dict)

    def get_issues_data(self):
        """
        Retrieves issue data from the GitHub API; uses the "range" configuration value
        to determine what indices of the issue paged list to look at and the
        "issues_fields" field to determine what information it should retrieve from
        each issues of interest
        """

        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        cmd_dict = self.ISSUE_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("issues_fields")
        paged_list = self.issues_paged_list

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = self.__check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                cur_issue = paged_list[i]
                cur_issue_num = self.ISSUE_CMD_DISPATCH["num"](self, cur_issue)

                cur_item_data = {
                    field: cmd_dict[field](self, cur_issue) for field in field_list
                }

                cur_entry = {cur_issue_num: cur_item_data}

                print(f"{cur_item_data}\n")

            except github.RateLimitExceededException:
                self.writer.concat_json("issues", data_dict)
                self.gh_sesh.sleep()

            else:
                data_dict.update(cur_entry)
                self.gh_sesh.print_rem_calls()

                i = i + 1

        self.writer.concat_json("issues", data_dict)

    def get_paged_list(self, list_type):
        """
        retrieve and store a paginated list from GitHub

        :param list_type str: type of paginated list to retrieve
        :rtype None: sets object member to paginated list object
        """
        job_repo = self.cfg.get_cfg_val("repo")

        try:
            # retrieve GitHub repo object
            repo_obj = self.gh_sesh.session.get_repo(job_repo)

            if list_type == "issues":
                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state="closed"
                )

                out_list = issues_paged_list

            else:
                pr_paged_list = repo_obj.get_pulls(
                    direction="asc", sort="created", state="closed"
                )

                out_list = pr_paged_list

            self.gh_sesh.print_rem_calls()

            return out_list

        except github.RateLimitExceededException:
            print()
            self.gh_sesh.sleep()
            # TODO remove exit and put all of this in a loop so that it retries when
            # sleep is finished
            sys.exit(1)

    def get_pr_data(self):
        """
        Retrieves PR data from the GitHub API; uses the "range" configuration value to
        determine what indices of the PR paged list to look at and the "pr_fields"
        field to determine what information it should retrieve from each PR of interest

        # TODO: add ability to start at a num, not index, e.g. PR #300 could be index 1
        """

        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        cmd_dict = self.PR_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("pr_fields")
        paged_list = self.pr_paged_list

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = self.__check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                cur_pr = paged_list[i]
                cur_pr_num = self.PR_CMD_DISPATCH["num"](self, cur_pr)
                cur_entry = {cur_pr_num: "Not Merged"}

                if cur_pr.merged:

                    # the expression below does several things:
                    # 1. the curly brackets indicate that this is a dictionary
                    # comprehension, so it creates a dict from the iterating expression
                    # inside
                    #
                    # 2. cmd_dict[field](cur_pr) uses the current "field" item in the
                    # field list, which the dict comprehension loops through, as the key
                    # to the cmd_dict, meaning that it grabs the val from the cmd_dict
                    # at that key. That val will be a function. It then sends cur_pr as
                    # a parameter to that function and stores the result.
                    #
                    # 3. field: cmd_dict[field](cur_pr) creates a key value pair, where
                    # the field, e.g. "num", is the key and the output found in point #2
                    # above is the key
                    #
                    # In sum, this takes the current PR and gets every field of
                    # information from the configuration file about this PR. If the user
                    # asks for "num" and "author_name" in the "PR fields" field of the
                    # config, this expression creates a dict containing those values for
                    # every PR. This same concept is used in the issues and commits
                    # getters
                    cur_item_data = {
                        field: cmd_dict[field](self, cur_pr) for field in field_list
                    }

                    # create dict entry using the issue num associated with the commit
                    # as the key
                    cur_entry = {cur_pr_num: cur_item_data}

                    print(f"{cur_entry}\n")

            except github.RateLimitExceededException:
                self.writer.concat_json("pr", data_dict)
                self.gh_sesh.sleep()

            else:
                data_dict.update(cur_entry)
                self.gh_sesh.print_rem_calls()

                i = i + 1

        self.writer.concat_json("pr", data_dict)


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

        self.commit_output = f"{repo_subdir}/commit_output.JSON"
        self.issues_output = f"{repo_subdir}/commit_output.JSON"
        self.pr_output = f"{repo_subdir}/commit_output.JSON"

        # for each file above, create it if it does not exist
        for file_path in (self.commit_output, self.issues_output, self.pr_output):
            if not os.path.exists(file_path):
                os.mknod(file_path)

    def concat_json(self, out_type, out_dict):
        """
        gets the desired output path, opens and reads any JSON data that may already be
        there, and recursively merges in-param data from the most recent round of API
        calls

        :param out_type str: the type of output being created, e.g. "commit", "issues"
        :param out_dict dict[unknown]: dict of data from round of API calls to merge and
        write
        """

        def __get_out_path(out_type):
            """
            [TODO:description]

            :param out_type [TODO:type]: [TODO:description]
            """
            # determine place we want to write our output to
            if out_type == "commit":
                return self.commit_output

            elif out_type == "issues":
                return self.issues_output

            return self.pr_output

        def __merge_dicts(add_dict, base_dict):
            """
            loops through keys in dictionary of data from round of API calls to merge
            their data into existing JSON data

            :param add_dict dict[unknown]: dict of data to be written
            :param base_dict dict[unknown]: dict of data already written to and read out
            from JSON file
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

        path = __get_out_path(out_type)

        # attempt to read JSON out of output file
        try:
            with open(path, "r") as json_outfile:
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
                json.dump(json_dict, json_outfile, ensure_ascii=True, indent=4)
