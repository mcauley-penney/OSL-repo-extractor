"""Commonly-used functionality related to Python dictionaries."""


def merge_dicts(base: dict, to_merge) -> dict:
    """
    Merge two dictionaries.

    Notes:
        syntax in 3.9 or greater is `base |= to_merge`. Pipe is the 'merge'
            operator, can be used in augmented assignment.

    Args:
        base (dict): dict to merge into.
        to_merge (dict | None): dict to dissolve into base dict.

    Returns:
        dict: if dict param to be merge is None, base dict
        param. Else, dict composed of merged dict params.

    """
    # sometimes getters return empty dictionaries. we want to merge if they
    # arent empty
    if to_merge:
        return {**base, **to_merge}

    return base


def merge_dicts_recursive(add_dict: dict, base_dict: dict) -> None:
    """
    Recursively merge two dictionaries.

    Notes:
        Credit to Paul Durivage
            https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    Args:
        add_dict (dict): dict of data to be merged
        base_dict (dict): dict to be merged into
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
