"""
This module is a storehouse for tools that derive social metrics from data
gathered from GitHub via the Extractor class
"""


def get_unique_discussants(issuecomment_dict: dict):
    """[TODO:description]"""
    discussants_set = set()

    for comment in issuecomment_dict.values():
        discussant_id = comment["discussant"]["id"]

        if isinstance(discussant_id, str):
            discussants_set.add(discussant_id)

    if not discussants_set:
        return {}

    return discussants_set


def get_issue_wordiness(issuecomment_dict: dict):
    """
    Count the amount of words over a length of 2 in each comment in an issue

    :param issuecomment_dict: dictionary of comments for an issue
    :type issuecomment_dict: dict
    """

    sum_wc = 0

    for comment in issuecomment_dict.values():
        body = comment["body"]

        # get all words greater in len than 2
        split_body = [word for word in body.split() if len(word) > 2]

        sum_wc += len(split_body)

    return sum_wc
