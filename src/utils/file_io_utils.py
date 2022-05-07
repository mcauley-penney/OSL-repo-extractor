"""
Utilites for reading from and writing to files.

json docs:
    https://docs.python.org/3/library/json.html
"""

import json
from json.decoder import JSONDecodeError
import os
import sys

from src.utils import dict_utils


def mk_json_outpath(out_dir: str, repo_title: str, output_type: str) -> str:
    """
    Create path to JSON file to write output data to.

    We cannot know if the user will always prepare output paths
    for us, so we must protect our operations by ensuring path
    existence

    :param out_dir: dir to init output file in
    :type out_dir: str
    :param repo_title: the name of the repo, e.g. "bar" in "foo/bar"
    :type repo_title: str
    :param output_type: Type of output being created, e.g. "issues" or "metrics"
    :type output_type: str
    :return: path to output file
    :rtype: str
    """
    path = f"{out_dir}/{repo_title}_{output_type}.json"

    # ensures that path exists, no exception handling required
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Using open() instead of mknode() allows this program to be portable;
    # mknode appears to be *nix specific. We can use "x" mode to ensure that
    # the open call is used exclusively for creating the file. If the file
    # exists, though, "x" mode raises a FileExistsError, which we must ignore.
    try:
        with open(path, "x", encoding="UTF-8") as fptr:
            fptr.close()

    except FileExistsError:
        pass

    return path


def read_json_text_into_dict(json_text: str) -> dict:
    """
    Convert text from JSON file into a python dict.

    :raises JSONDecodeError: contents of str param are not valid JSON

    :param json_text: text from JSON file
    :type json_text: str
    :return: dictionary of contents from JSON file
    :rtype: dict
    """
    try:
        json_dict = json.loads(json_text)

    # if no JSON content exists there, ignore. In this context, it simply
    # means that we are writing JSON to a new file
    except JSONDecodeError:
        return {}

    else:
        return json_dict


def read_file_line(in_path: str) -> str:
    """
    Read a single line from the top of a text file.

    Used for reading personal access tokens (PATs) out of auth file.

    :raises FileNotFoundError: file does not exist at path

    :param in_path: path to file to read line from
    :type in_path: str
    :return: line from file, stripped of whitespace and newlines
    :rtype: str
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

    :param in_path: path to JSON file to read from
    :type in_path: str
    :return: dictionary constructed from JSON contents
    :rtype: dict
    """
    json_text = read_file_into_text(in_path)

    json_dict = read_json_text_into_dict(json_text)

    return json_dict


def read_file_into_text(in_path: str) -> str:
    """
    Read file contents into string.

    Used for reading JSON data out of JSON files.

    :raises FileNotFoundError: no file found at given path

    :param in_path: path to file to read contents from
    :type in_path: str
    :return: text from file
    :rtype: str
    """
    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            json_text = file_obj.read()

    except FileNotFoundError:
        print(f'\nFile at "{in_path}" not found!')
        sys.exit(1)

    else:
        return json_text


def write_dict_to_jsonfile(out_dict: dict, out_path: str) -> None:
    """
    Write given Python dictionary to output file as JSON.

    :raises FileNotFoundError: no file found at given path

    :param out_dict: dictionary to write as JSON
    :type out_dict: dict
    :param out_path: path to write output to
    :type out_path: str
    """
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

    :param out_dict: dict of data from round of API calls to merge and write
    :type out_dict: dict
    :param out_path: path to output file
    :type out_path: str
    """
    json_dict = {}

    # attempt to read JSON out of output file. Will return empty dict if no
    # valid Json is found
    json_dict = read_jsonfile_into_dict(out_path)

    # recursively merge all dicts and nested dicts in both dictionaries
    dict_utils.merge_dicts_recursive(out_dict, json_dict)

    # write JSON content back to file
    write_dict_to_jsonfile(json_dict, out_path)
