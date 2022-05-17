"""
Exposes schema and related getter functionality to Cfg class.

This module is intended to provide easy access to the extractor's

    1. getter functionality
    2. command dispatch tables
    3. configuration schema

so that a user may be able to have an easier time adding functionality for
their own uses, such as adding a new getter function.

To add a new piece of functionality, the user has to make a few modifications:

    1. create a new getter function which accesses items provided by PyGithub
    2. add that function to the appropriate subdictionary in the command
        dispatch table: {"field name to access function": function reference}
            • this allows the configuration schema to know which fields are
                acceptable

You *do not* need to modify the schema to add a new getter. You *only* need
to create the function and add it to the dispatch table in the appropriate
item subdictionary.

Resources:

    • PyGithub documentation:
        https://pygithub.readthedocs.io/en/latest/github.html?highlight=main

    • See cerberus documentation for schema rules:
        https://docs.python-cerberus.org/en/stable/index.html

    • introduction to dispatch tables:
        https://betterprogramming.pub/dispatch-tables-in-python-d37bcc443b0b
"""
from repo_extractor import conf

TIME_FMT = "%D, %I:%M:%S %p"


def get_item_data(user_cfg: conf.Cfg, item_type: str, cur_item) -> dict:
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
    field_list = user_cfg.get_cfg_val(f"{item_type}_fields")

    cmd_tbl = _cmd_tbl_dict[item_type]

    # when called, this will resolve to various function calls, e.g.
    # "body": cmd_tbl["body"](cur_PR)
    return {field: cmd_tbl[field](cur_item) for field in field_list}


def _clean_str(str_to_clean: str | None) -> str:
    """
    If given a valid string, strip it of whitespace and carriage returns.

    Args:
        str_to_clean (str|None): string to clean and return

    Returns:
        str: if param string is empty or None, returns "NaN". Else,
        return param string stripped of carriage returns and whitespace.
    """
    if str_to_clean is None or str_to_clean == "":
        return "Nan"

    output_str = str_to_clean.replace("\r", "")
    output_str = output_str.replace("\n", "")

    return output_str.strip()


def _get_body(api_obj) -> str:
    return _clean_str(api_obj.body)


def _get_commit_author_name(api_obj) -> str:
    return api_obj.commit.author.name


def _get_commit_committer(api_obj) -> str:
    return api_obj.commit.committer.name


def _get_commit_date(api_obj) -> str:
    return api_obj.commit.author.date.strftime(TIME_FMT)


def _get_commit_files(commit_obj) -> dict:
    """
    For the list of files modified by a commit, return a list of qualities.

    Note:
        If a list of files is too large, it will be returned as
        a paginatied list. See note about the list length constraints
        at https://docs.github.com/en/rest/reference/commits#get-a-commit.
        As of right now, this situation is not handled here.

    Args:
        commit_obj (github.Commit): commit to get file change data from

    Returns:
        dict: dict of data about file changes made by the given PR
    """
    file_list = commit_obj.files

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


def _get_closed_time(issue) -> str:
    """
    Get the datetime an API object was closed, if closed.

    Args:
        api_obj (Github.Issue): API object to get closed time of

    Returns:
        str: datetime string of API object closure or "NaN"
    """
    if issue.closed_at is not None:
        return issue.closed_at.strftime(TIME_FMT)

    return "NaN"


def _get_issue_comments_quant(issue_obj):
    return issue_obj.comments


def _get_title(api_obj) -> str:
    return api_obj.title


def _get_userid(api_obj) -> str:
    return str(api_obj.user.id)


def _get_userlogin(api_obj) -> str:
    return _clean_str(api_obj.user.login)


# Initialize map of strings to function references; a
# dispatch table. This allows us to call a function
# using a string, by saying
#
#       cmd_tbl_dict[type][function name]()
#
# To get an issue body, for example, we can either say
#
#       cmd_tbl_dict["issue"]["body"]()
#
# Items which map to get_item_data are intended to be
# recursively gathered; mapping to get_item_data does
# nothing, and those items which are will be caught in
# get_item_data by a conditional which checks for
# field lists nested in other field lists, e.g.
# "user" in "issue"

_cmd_tbl_dict: dict = {
    # top-level actors
    "issue": {
        "body": _get_body,
        "closed": _get_closed_time,
        "num_comments": _get_issue_comments_quant,
        "title": _get_title,
        "userid": _get_userid,
        "userlogin": _get_userlogin,
    },
    "comments": {
        "body": _get_body,
        "userid": _get_userid,
        "userlogin": _get_userlogin,
    },
    "pr": {},
    "commit": {
        "commit_author_name": _get_commit_author_name,
        "committer": _get_commit_committer,
        "commit_date": _get_commit_date,
        "commit_files": _get_commit_files,
        "commit_message": _get_commit_msg,
        "commit_sha": _get_commit_sha,
    },
}

# Schema used to validate user-provided configuration.
# This acts as a template to judge whether the user cfg
# is acceptable to the program. This *does not* need to
# be modified to add new getter functionality
cfg_schema: dict = {
    "repo": {"type": "string"},
    "auth_file": {"type": "string"},
    "state": {"allowed": ["closed", "open"], "type": "string"},
    "range": {"min": [0, 0], "schema": {"type": "integer"}, "type": "list"},
    "output_dir": {"type": "string"},
}

# loop over keys in cmd_tbl_dict and init corresponding
# entries in the configuration schema
for key, _ in _cmd_tbl_dict.items():
    cfg_schema[f"{key}_fields"] = {
        "allowed": [*_cmd_tbl_dict[key]],
        "schema": {"type": "string"},
        "type": "list",
    }
