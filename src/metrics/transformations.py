"""
This module is a storehouse for tools that derive social metrics from data
gathered from GitHub via the Extractor class
"""


def get_unique_discussants(issuecomment_dict: dict):
    """[TODO:description]"""
    discussants_set = set()

    # unpack each dict into tuple?

    for comment in issuecomment_dict.values():
        discussant_id = comment["discussant"]["id"]

        if isinstance(discussant_id, str):
            discussants_set.add(discussant_id)

    return discussants_set


def get_issue_wordiness():
    """[TODO:description]"""
