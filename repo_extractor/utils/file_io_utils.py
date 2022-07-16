"""
Utilites for reading from and writing to files.

json docs:
    https://docs.python.org/3/library/json.html
"""

import json
from json.decoder import JSONDecodeError
import os
import sys

from repo_extractor.utils import dict_utils


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
    # exists, though, "x" mode raises a FileExistsError, which we can/must
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
    Write given Python dictionary to output file as JSON.

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
    # empty dict if no valid Json is found
    json_dict = read_jsonfile_into_dict(out_path)

    # recursively merge all dicts and nested dicts in both dictionaries
    dict_utils.merge_dicts_recursive(json_dict, out_dict)

    # write JSON content back to file
    write_dict_to_jsonfile(json_dict, out_path)
