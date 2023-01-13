"""
Common utilites for the repository extractor.

Includes:
    - dictionary handling
    - file io

json docs:
    https://docs.python.org/3/library/json.html
"""

import json
from json.decoder import JSONDecodeError
import os
import sys


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


def merge_dicts_recursive(base_dict: dict, add_dict: dict) -> None:
    """
    Recursively merge two dictionaries.

    Notes:
        Credit to Paul Durivage
            https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    Args:
        base_dict (dict): dict to be merged into
        add_dict (dict): dict of data to be merged
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
            merge_dicts_recursive(base_dict[key], add_dict[key])

        else:
            # assign the new value from the last round of calls to the existing
            # key
            base_dict[key] = add_dict[key]


def mk_json_outpath(out_path: str):
    """
    Create path to JSON file to write output data to.

    We cannot know if the user will always prepare output paths
    for us, so we must protect our operations by ensuring path
    existence

    Args:
        out_dir (str): dir to init output file in.
        repo_title (str): the name of the repo, e.g. "bar" in "foo/bar".
        output_type (str): type of output being created.

    Raises:
        FileExistsError: if the file that we are attempting to
        create already exists, simply move on. The extractor
        knows how to update already existing JSON outputs.

    Returns:
        str: path to output file
    """
    # ensures that path exists, no exception handling required
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Using open() instead of mknode() allows this program to be portable;
    # mknode appears to be *nix specific. We can use "x" mode to ensure that
    # the open call is used exclusively for creating the file. If the file
    # exists, though, "x" mode raises a FileExistsError, which we can
    # ignore.
    try:
        with open(out_path, "x", encoding="UTF-8") as fptr:
            fptr.close()

    except FileExistsError:
        pass


def _read_json_into_text(in_path: str) -> str:
    """
    Read file contents into string.

    Used for reading JSON data out of JSON files.

    Args:
        in_path (str): path to file to read contents from.

    Raises:
        FileNotFoundError: hard exit if a file cannot be found.

    Returns:
        str: text from file.
    """
    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            json_text = file_obj.read()

    except FileNotFoundError:
        print(f'\nFile at "{in_path}" not found!')
        sys.exit(1)

    else:
        return json_text


def read_file_line(in_path: str) -> str:
    """
    Read a single line from the top of a text file.

    Used for reading personal access tokens out of a file.

    Args:
        in_path (str): path to file to read line from.

    Raises:
        FileNotFoundError: hard exit if a file cannot be found.

    Returns:
        str: line from file, stripped of whitespace and newlines.
    """
    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            file_text = file_obj.readline()

    except FileNotFoundError:
        print(f'\nFile at "{in_path}" not found!')
        sys.exit(1)

    else:
        return file_text.strip().strip("\n")


def read_jsonfile_into_dict(in_path: str) -> dict:
    """
    Read the contents of the provided JSON file into a dictionary.

    Args:
        in_path (str): path to JSON file to read from.

    Returns:
        dict: dictionary constructed from JSON contents.
    """
    json_text = _read_json_into_text(in_path)

    json_dict = read_jsontext_into_dict(json_text)

    return json_dict


def read_jsontext_into_dict(json_text: str) -> dict:
    """
    Convert text from JSON file into a python dict.

    Args:
        json_text (str): text from JSON file.

    Raises:
        JSONDecodeError: if no valid JSON content exists, ignore.
            In this context, it simply means that we are writing
            JSON to a new file.

    Returns:
        dict: dictionary constructed from JSON contents.
    """
    try:
        json_dict = json.loads(json_text)

    except JSONDecodeError:
        return {}

    else:
        return json_dict


def write_dict_to_jsonfile(out_dict: dict, out_path: str) -> None:
    """
    Ensure output file exists and write Python dictionary to it as JSON.

    Args:
        out_dict (dict): dictionary to write as JSON.
        out_path (str): path to write output to.

    Raises:
        FileNotFoundError: no file found at given path.
    """
    mk_json_outpath(out_path)

    try:
        with open(out_path, "w", encoding="UTF-8") as json_outfile:
            json.dump(out_dict, json_outfile, ensure_ascii=False, indent=4)

    except FileNotFoundError:
        print(f"\nFile at {out_path} not found!")
        sys.exit(1)


def write_merged_dict_to_jsonfile(out_dict: dict, out_path: str) -> None:
    """
    Recursively merge dictionaries and write them to an output JSON file.

    Get the desired output path, open and read any JSON data that may
    already be there, and recursively merge in param data from the
    most recent round of API calls.

    Args:
        out_dict (dict): dict of data from round of API calls
            to merge and write.
        out_path (str): path to output file.
    """
    # attempt to read JSON out of output file. Will return
    # empty dict if no valid json is found
    json_dict = read_jsonfile_into_dict(out_path)

    # recursively merge all dicts and nested dicts in both dictionaries
    dict_utils.merge_dicts_recursive(json_dict, out_dict)

    # write JSON content back to file
    write_dict_to_jsonfile(json_dict, out_path)
