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

# 0000-00-00T00:00:00Z
TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _get_body(api_obj) -> str:
    return api_obj.body


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

    commit_files: list = []
    commit_patches: list = []
    commit_statuses: list = []
    commit_adds: int = 0
    commit_changes: int = 0
    commit_deletions: int = 0

    for file in file_list:
        commit_files.append(file.filename)
        commit_patches.append(file.patch)
        commit_statuses.append(file.status)
        commit_adds += int(file.additions)
        commit_changes += int(file.changes)
        commit_deletions += int(file.deletions)

    return {
        "additions": commit_adds,
        "deletions": commit_deletions,
        "changes": commit_changes,
        "file_list": commit_files,
        "status": commit_statuses,
        "patch_text": commit_patches,
    }


def _get_commit_msg(commit_obj) -> str:
    return commit_obj.commit.message


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


def _get_created_time(api_obj) -> str:
    """
    Get the datetime an issue was created at.

    Args:
        issue (Github.Issue): PyGithub issue to get closed time of

    Returns:
        str: datetime string of issue creation
    """
    return api_obj.created_at.strftime(TIME_FMT)


def _get_issue_comments_quant(issue_obj):
    return issue_obj.comments


def __get_nameduser_name(api_obj_nameduser):
    return api_obj_nameduser.name


def _get_title(api_obj) -> str:
    return api_obj.title


def _get_userid(api_obj) -> str:
    return str(api_obj.user.id)


def _get_userlogin(api_obj) -> str:
    return api_obj.user.login


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
        "created_at": _get_created_time,
    },
    "commits": {
        "author_name": _get_commit_author_name,
        "committer": _get_commit_committer,
        "date": _get_commit_date,
        "files": _get_commit_files,
        "message": _get_commit_msg,
        "sha": _get_commit_sha,
    },
    "issues": {
        "body": _get_body,
        "closed_at": _get_closed_time,
        "created_at": _get_created_time,
        "num_comments": _get_issue_comments_quant,
        "title": _get_title,
        "userid": _get_userid,
        "userlogin": _get_userlogin,
    },
}


REPO_SLUG_REGEX = r"^[^/\s]+/[^/\s]+$"
STATE_ALLOWED = ["open", "closed", "all"]


def _required(rule: dict) -> dict:
    """Return a Cerberus rule with an explicit required flag."""
    return {**rule, "required": True}


def _optional(rule: dict) -> dict:
    """Return a Cerberus rule with an explicit optional flag."""
    return {**rule, "required": False}


def _build_string_list_rule(*, required: bool) -> dict:
    """Build a list-of-strings validation rule."""
    required_rule = _required if required else _optional

    return required_rule(
        {
            "type": "list",
            "schema": {"type": "string"},
        }
    )


def _build_field_list_rule(field_type: str, *, required: bool) -> dict:
    """Build a field-selector list rule for the given extractor item type."""
    required_rule = _required if required else _optional

    return required_rule(
        {
            "type": "list",
            "schema": {
                "type": "string",
                "allowed": [*cmd_tbl[field_type]],
            },
        }
    )


def _build_fields_rule(*, required: bool, allow_partial: bool) -> dict:
    """
    Build a nested fields dictionary rule.

    Args:
        required (bool): whether the fields dict itself must be present.
        allow_partial (bool): whether nested issue/comment/commit selectors
            may be omitted. Defaults must define all selectors; target-level
            overrides may define only the selectors they wish to override.
    """
    required_rule = _required if required else _optional
    nested_required = not allow_partial

    return required_rule(
        {
            "type": "dict",
            "schema": {
                "issues": _build_field_list_rule("issues", required=nested_required),
                "comments": _build_field_list_rule(
                    "comments",
                    required=nested_required,
                ),
                "commits": _build_field_list_rule(
                    "commits",
                    required=nested_required,
                ),
            },
        }
    )


def _validate_target_range(field: str, value: dict, error) -> None:
    """
    Validate logical constraints on a target range object.

    The range schema ensures that integer values are positive. This callback
    additionally ensures that the optional end bound is not lower than start.
    """
    start = value.get("start")
    end = value.get("end")

    if isinstance(start, int) and isinstance(end, int) and end < start:
        error(field, '"end" must be greater than or equal to "start"')


def _build_range_rule(*, required: bool) -> dict:
    """Build a target range rule with object-based start/end bounds."""
    required_rule = _required if required else _optional

    return required_rule(
        {
            "type": "dict",
            "check_with": _validate_target_range,
            "schema": {
                "start": _required({"type": "integer", "min": 1}),
                "end": _optional({"type": "integer", "min": 1, "nullable": True}),
            },
        }
    )


def _build_state_rule(*, required: bool) -> dict:
    """Build a rule for issue/PR state selection."""
    required_rule = _required if required else _optional

    return required_rule({"type": "string", "allowed": STATE_ALLOWED})


def _build_repo_slug_rule(*, required: bool) -> dict:
    """Build a rule for GitHub repo slugs in owner/name format."""
    required_rule = _required if required else _optional

    return required_rule({"type": "string", "regex": REPO_SLUG_REGEX})


defaults_schema = {
    "state": _build_state_rule(required=True),
    "labels": _build_string_list_rule(required=True),
    "fields": _build_fields_rule(required=True, allow_partial=False),
}

target_schema = {
    "repo": _build_repo_slug_rule(required=True),
    "range": _build_range_rule(required=True),
    "state": _build_state_rule(required=False),
    "labels": _build_string_list_rule(required=False),
    "fields": _build_fields_rule(required=False, allow_partial=True),
}

# Schema used to validate user-provided configuration.
# This acts as a template to judge whether the user cfg
# is acceptable to the program.
cfg_schema: dict = {
    "auth_path": _required({"type": "string"}),
    "output_path": _required({"type": "string"}),
    "defaults": _required(
        {
            "type": "dict",
            "schema": defaults_schema,
        }
    ),
    "targets": _required(
        {
            "type": "list",
            "minlength": 1,
            "schema": {
                "type": "dict",
                "schema": target_schema,
            },
        }
    ),
}
