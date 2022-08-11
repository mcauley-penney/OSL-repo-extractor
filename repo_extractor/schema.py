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

    • See Cerberus documentation for schema rules:
        https://docs.python-cerberus.org/en/stable/index.html

    • introduction to dispatch tables:
        https://betterprogramming.pub/dispatch-tables-in-python-d37bcc443b0b
"""

TIME_FMT = "%D, %I:%M:%S %p"


def _sanitize_str(in_str) -> str:
    """
    If given a valid string, strip it of whitespace and carriage returns.

    Args:
        str_to_clean (str|None): string to clean and return

    Returns:
        str: if param string is empty or None, returns "NaN". Else,
        return param string stripped of carriage returns and whitespace.
    """
    if in_str is None or in_str == "":
        return "NaN"

    for esc_char in ("\r", "\n"):
        in_str = in_str.replace(esc_char, "")

    return in_str.strip()


def _get_body(api_obj) -> str:
    return _sanitize_str(api_obj.body)


def _get_commit_author_name(commit_obj) -> str:
    return __get_nameduser_name(commit_obj.commit.author)


def _get_commit_committer(commit_obj) -> str:
    return __get_nameduser_name(commit_obj.commit.committer)


def _get_commit_date(commit_obj) -> str:
    return commit_obj.commit.author.date.strftime(TIME_FMT)


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
        "patch_text": _sanitize_str(commit_patch_text),
        "removals": commit_removes,
        "status": _sanitize_str(quoted_commit_status_str),
    }


def _get_commit_msg(commit_obj) -> str:
    return _sanitize_str(commit_obj.commit.message)


def _get_commit_sha(commit_obj) -> str:
    return commit_obj.sha


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


def _get_created_time(issue) -> str:
    """
    Get the datetime an issue was created at.

    Args:
        issue (Github.Issue): PyGithub issue to get closed time of

    Returns:
        str: datetime string of issue creation
    """
    return issue.created_at.strftime(TIME_FMT)


def _get_issue_comments_quant(issue_obj):
    return issue_obj.comments


def __get_nameduser_name(api_obj_nameduser):
    return api_obj_nameduser.name


def _get_title(api_obj) -> str:
    return api_obj.title


def _get_userid(api_obj) -> str:
    return str(api_obj.user.id)


def _get_userlogin(api_obj) -> str:
    return _sanitize_str(api_obj.user.login)


# Initialize map of strings to function references; a
# dispatch table. This allows us to call a function
# using a string, by saying
#
#       cmd_tbl_dict[type][function name]()
#
# To get an issue body, for example, we can either say
#
#       cmd_tbl_dict["issue"]["body"]()
cmd_tbl: dict = {
    # top-level actors
    "comments": {
        "body": _get_body,
        "userid": _get_userid,
        "userlogin": _get_userlogin,
    },
    "commits": {
        "author_name": _get_commit_author_name,
        "committer": _get_commit_committer,
        "date": _get_commit_date,
        "files": _get_commit_files,
        "message": _get_commit_msg,
        "sha": _get_commit_sha,
    },
    "issue": {
        "body": _get_body,
        "closed_at": _get_closed_time,
        "created_at": _get_created_time,
        "num_comments": _get_issue_comments_quant,
        "title": _get_title,
        "userid": _get_userid,
        "userlogin": _get_userlogin,
    },
}


_str_type = {"type": "string"}


# TODO: expand comment explaining this.
# Create dictionary out of each dict in the command
# table which discusses what types of fields are
# allowed in the configuration schema.
#
# [*_] = create a list from the keys of the unpacked
#        dict comprehension operand dict, e.g. _cmd_tbl_dict
issue_fields_schema = {
    key: {
        "allowed": [*_],
        "schema": _str_type,
        "type": "list",
    }
    for key, _ in cmd_tbl.items()
}

# Schema used to validate user-provided configuration.
# This acts as a template to judge whether the user cfg
# is acceptable to the program.
cfg_schema: dict = {
    "auth_path": _str_type,
    "repo": _str_type,
    "output_path": _str_type,
    "repo_data": {
        "type": "dict",
        "schema": {
            **issue_fields_schema,
            "state": {**_str_type, "allowed": ["closed", "open"]},
            "range": {
                "nullable": True,
                "min": [0, 0],
                "schema": {"type": "integer"},
                "type": "list",
            },
        },
    },
}
