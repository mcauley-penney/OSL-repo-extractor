"""TODO:"""


def merge_dicts(base: dict, to_merge) -> dict:
    """
    Merge two dictionaries
    NOTES:
        • syntax in 3.9 or greater is "base |= to_merge"
            • pipe is the "merge" operator, can be used in augmented assignment

    :param base: dict to merge into
    :type base: dict
    :param to_merge: dict to dissolve into base dict
    :type to_merge: dict
    :return: base dict
    :rtype: dict
    """

    # sometimes getters return empty dictionaries. we want to merge if they
    # arent empty
    if to_merge:
        return {**base, **to_merge}

    return base


def merge_dicts_recursive(add_dict, base_dict) -> None:
    """
    loops through keys in dictionary of data from round of API calls to merge
    their data into existing JSON data

    credit to Paul Durivage: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    :param add_dict dict[unknown]: dict of data to be written

    :param base_dict dict[unknown]: dict of data already written to and read out
    from JSON file

    :rtype None: merges param dicts
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
            merge_dicts_recursive(add_dict[key], base_dict[key])

        else:
            # assign the new value from the last round of calls to the existing
            # key
            base_dict[key] = add_dict[key]
