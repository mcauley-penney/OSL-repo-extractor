"""
the extractor module provides and exposes functionality to mine GitHub repositories
"""

import json
from json.decoder import JSONDecodeError
import logging
import os
import sys
import github
from base import conf, sessions, utils


TIME_FMT = "%D, %I:%M:%S %p"


def __get_body(api_obj):
    return utils.clean_str(api_obj.body)


def __get_closed_time(api_obj):
    if api_obj is not None:
        return api_obj.closed_at.strftime(TIME_FMT)

    return "NaN"


def __get_issue_comments(issue_obj):

    comments_paged_list = issue_obj.get_comments()

    if comments_paged_list.totalCount != 0:
        # get body from each comment, strip of whitespace, and join w/ special char
        comment_str = " =||= ".join(
            comment.body.strip() for comment in comments_paged_list
        )

        # strip comment string of \n, \r, and whitespace again
        return utils.clean_str(comment_str)

    return "NaN"


def __get_num(api_obj):
    return str(api_obj.number)


def __get_pr_merged(pr_obj):
    return pr_obj.merged


def __get_title(api_obj):
    return api_obj.title


def __get_username(api_obj):
    return utils.clean_str(api_obj.user.name)


def __get_userlogin(api_obj):
    return utils.clean_str(api_obj.user.login)


def __get_commit_auth_name(api_obj):
    return api_obj.commit.author.name


def __get_commit_auth_date(api_obj):
    return api_obj.commit.author.date.strftime(TIME_FMT)


def __get_commit_committer(api_obj):
    return api_obj.commit.committer.name


def __get_commit_files(api_obj):
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
        "patch_text": utils.clean_str(commit_patch_text),
        "removals": commit_removes,
        "status": utils.clean_str(quoted_commit_status_str),
    }


def __get_commit_msg(api_obj):
    return api_obj.commit.message


def __get_commit_sha(api_obj):
    return api_obj.sha


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
    "issue_comments": __get_issue_comments,
    "num": __get_num,
    "title": __get_title,
    "userlogin": __get_userlogin,
    "username": __get_username,
}

PR_CMD_DISPATCH = {
    "body": __get_body,
    "closed": __get_closed_time,
    "num": __get_num,
    "pr_merged": __get_pr_merged,
    "title": __get_title,
    "userlogin": __get_userlogin,
    "username": __get_username,
}

# see cerberus documentation for schema rules
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


class Extractor:
    """
    # TODO:

    1. attempt to write all outputs to one file, e.g. write commit data and issue data,
    both with PR/issue num as keys, to the same place and see it they update. See lines
    around 444 for output file path creation

    TODO: update
    The extractor class contains and executes GitHub REST API
    functionality. It holds onto a configuration object, initiates and
    holds onto the connection to GitHub, asks for information from GitHub and
    stores it in a dataset object, and has the ability to write that dataeset
    to JSON or a database.
    """

    def __init__(self, cfg_path) -> None:
        """
        TODO: Description

        :rtype None: initializes extractor object
        """

        self.__logger = logging.getLogger(__name__)

        self.__logger.info("Beginning extractor init, instantiating cfg...\n")

        # initialize configuration object
        self.cfg = conf.Cfg(cfg_path, CFG_SCHEMA)

        # initialize authenticated GitHub session
        self.gh_sesh = sessions.GithubSession(self.cfg.get_cfg_val("auth_file"))

        # initialize writer object
        self.writer = Writer(
            self.cfg.get_cfg_val("output_dir"), self.cfg.get_cfg_val("repo")
        )

        self.pr_paged_list = self.get_paged_list("pr")
        self.issues_paged_list = self.get_paged_list("issues")

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

    def get_issues_data(self):
        """
        For every item in the list of items desired from the API, get the
        function from the dictionary of available API calls, execute that
        function, and store the returned value.
        """

        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        cmd_dict = ISSUE_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("issues_fields")
        paged_list = self.issues_paged_list

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = utils.check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                cur_issue = paged_list[i]
                cur_issue_num = ISSUE_CMD_DISPATCH["num"](cur_issue)

                cur_item_data = {
                    field: cmd_dict[field](cur_issue) for field in field_list
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

    def get_pr_data(self):
        """
        [TODO:description]

        """
        data_dict = {}
        val_range = self.cfg.get_cfg_val("range")

        cmd_dict = PR_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("pr_fields")
        paged_list = self.pr_paged_list

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = utils.check_row_quant_safety(paged_list, i, val_range[1])

        # TODO: add ability to start at a num, not index, e.g. PR #300 could be index 1
        while i < safe_row:
            try:
                cur_pr = paged_list[i]
                cur_pr_num = PR_CMD_DISPATCH["num"](cur_pr)
                cur_entry = {cur_pr_num: "Not Merged"}

                if cur_pr.merged:

                    cur_item_data = {
                        field: cmd_dict[field](cur_pr) for field in field_list
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

    def get_commit_data(self):
        """
        [TODO:description]

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
        cmd_dict = COMMIT_CMD_DISPATCH

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = utils.check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                # reset
                cur_pr = paged_list[i]
                cur_pr_num = PR_CMD_DISPATCH["num"](cur_pr)
                cur_entry = {cur_pr_num: "Not Merged"}

                if cur_pr.merged:

                    last_commit = __get_last_commit(cur_pr)

                    # if there are files changed for this commit
                    if len(last_commit.files) > 0:

                        # get all data from that commit
                        cur_item_data = {
                            field: cmd_dict[field](last_commit) for field in field_list
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


class Writer:
    """TODO: docs"""

    def __init__(self, output_dir, full_repo) -> None:
        """
        [TODO:description]

        :param output_dir [TODO:type]: [TODO:description]
        :param full_repo [TODO:type]: [TODO:description]
        :rtype None: [TODO:description]
        """

        # lop repo str off of full repo info, e.g. owner/repo
        repo_name = full_repo.rsplit("/", 1)[1]

        # init output subdir for this repo and hold onto it
        self.repo_subdir = f"{output_dir}/{repo_name}"

        self.commit_output = f"{self.repo_subdir}/commit_output.JSON"
        self.issues_output = f"{self.repo_subdir}/commit_output.JSON"
        self.pr_output = f"{self.repo_subdir}/commit_output.JSON"

        # create output directory only if it does not exist
        os.makedirs(self.repo_subdir, exist_ok=True)

    def concat_json(self, out_type, out_dict):
        """
        [TODO:description]

        :param out_type [TODO:type]: [TODO:description]
        :param out_dict [TODO:type]: [TODO:description]
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
            [TODO:description]

            :param add_dict [TODO:type]: [TODO:description]
            :param base_dict [TODO:type]: [TODO:description]
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

            # write sorted JSON content back to file
            with open(path, "w") as json_outfile:
                json.dump(json_dict, json_outfile, ensure_ascii=True, indent=4)
