"""
the extractor module provides and exposes functionality to mine GitHub repositories
"""


import logging
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
    return api_obj.number


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

    return [
        commit_file_list,
        commit_adds,
        commit_changes,
        commit_patch_text,
        commit_removes,
        quoted_commit_status_str,
    ]


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


COMMON_CMD_DISPATCH = {
    "body": __get_body,
    "closed": __get_closed_time,
    "issue_comments": __get_issue_comments,
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
        "allowed": [*COMMON_CMD_DISPATCH],
        "schema": {"type": "string"},
        "type": "list",
    },
    "pr_fields": {
        "allowed": [*COMMON_CMD_DISPATCH],
        "schema": {"type": "string"},
        "type": "list",
    },
    "pr_json": {"type": "string"},
}


class Extractor:

    """
    # TODO:
    #   1. data writing methods
    #   2. consider consolidating dispatch dicts into one. For it to work in the list
    #   generators, would need to pass all relevant api objects into functions, e.g. to
    #   get the PR num and then commit data in the list generator in get_commit_data,
    #   the getter functions would need to be passed the correct items in the function
    #   call, e.g. cur_item_data += [
                            cmd_dict[field](relevant_commit) for field in field_list
                        ]

        would require both the PR and "relevant_commit" in that call

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

        # initialize tools
        self.cfg = conf.Cfg(cfg_path, CFG_SCHEMA)
        self.gh_sesh = sessions.GithubSession(self.cfg.get_cfg_val("auth_file"))

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
        # use generic logging msg unless we don't have too many params
        # self.__logger.info(utils.LOG_DICT["G_DATA_ISSUE"])

        data_list = []
        val_range = self.cfg.get_cfg_val("range")

        cmd_dict = COMMON_CMD_DISPATCH
        field_list = self.cfg.get_cfg_val("issues_fields")
        paged_list = self.issues_paged_list

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = utils.check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                cur_item = paged_list[i]
                cur_item_data = [cmd_dict[field](cur_item) for field in field_list]
                print(f"{cur_item_data}\n")

            except github.RateLimitExceededException:
                self.gh_sesh.sleep()

            else:
                data_list.append(cur_item_data)
                self.gh_sesh.print_rem_calls()

                i = i + 1

    def get_pr_data(self):
        """
        [TODO:description]

        """
        data_list = []
        val_range = self.cfg.get_cfg_val("range")

        paged_list = self.pr_paged_list
        field_list = self.cfg.get_cfg_val("pr_fields")
        cmd_dict = COMMON_CMD_DISPATCH

        # must begin at first item of range
        i = val_range[0]

        # adjust amount of rows to get if unsafe
        safe_row = utils.check_row_quant_safety(paged_list, i, val_range[1])

        while i < safe_row:
            try:
                cur_item_data = []
                cur_item = paged_list[i]

                if cur_item.merged:
                    cur_item_data = [cmd_dict[field](cur_item) for field in field_list]
                    print(f"{cur_item_data}\n")

            except github.RateLimitExceededException:
                self.gh_sesh.sleep()

            else:
                data_list.append(cur_item_data)
                self.gh_sesh.print_rem_calls()

                i = i + 1

    def get_commit_data(self):
        """
        [TODO:description]

        """

        data_list = []
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
                cur_item_data = []
                cur_pr = paged_list[i]

                if cur_pr.merged:

                    # get paginated list of commits for PR at current index
                    cur_commit_list = cur_pr.get_commits()

                    # get index of commit we want from len of paginated list of commits
                    cur_commit_list_len = cur_commit_list.totalCount - 1

                    # use that index to get the commit we are interested in
                    relevant_commit = cur_commit_list[cur_commit_list_len]

                    if len(relevant_commit.files) > 0:

                        cur_item_data.append(cur_pr.number)

                        # get all data from that commit
                        cur_item_data += [
                            cmd_dict[field](relevant_commit) for field in field_list
                        ]

                    print(f"{cur_item_data}\n")

            except github.RateLimitExceededException:
                self.gh_sesh.sleep()

            else:
                data_list.append(cur_item_data)
                self.gh_sesh.print_rem_calls()

                i = i + 1
