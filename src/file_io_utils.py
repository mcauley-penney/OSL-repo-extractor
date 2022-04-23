"""The io module provides I/O functionality to the Extractor class"""

import json
from json.decoder import JSONDecodeError
import os
import sys

from src import dict_utils


def mk_json_outpath(out_dir: str, repo_title: str, output_type: str) -> str:
    """
    TODO

    We cannot know if the user will always prepare output paths for us, so we
    must protect our operations by ensuring path existence

    :param out_dir:
    :type out_dir: str
    :param repo_title:
    :type repo_title: str
    :param output_type:
    :type output_type: str
    :return:
    :rtype:
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


def read_bytes_into_dict(json_text: str) -> dict:
    """
    TODO:

    :param json_text:
    :type json_text:
    :return:
    :rtype:
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
    read a single line from the top of a text file.
    Used for reading personal access tokens (PATs) out of auth file

    :raises FileNotFoundError: file does not exist at path
    :param auth_file_path str: path to auth file
    :rtype pat_list list[str]: text lines from auth file
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
    open the provided JSON file and read its contents out into a dictionary

    :raises FileNotFoundError: file does not exist at path
    :param cfg_file str: path name to a JSON configuration file
    :rtype dict: dictionary constructed from JSON string
    """

    json_text = read_jsonfile_into_bytes(in_path)

    json_dict = read_bytes_into_dict(json_text)

    return json_dict


def read_jsonfile_into_bytes(in_path: str) -> str:
    """
    TODO:

    :param in_path:
    :type in_path: str
    :return:
    :rtype:
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
    write given Python dictionary to output file as JSON

    :raises FileNotFoundError: file does not exist at path
    :param out_dict dict: dictionary to write as JSON
    :param out_path str: path to write output to
    :rtype None
    """
    try:
        with open(out_path, "w", encoding="UTF-8") as json_outfile:
            json.dump(out_dict, json_outfile, ensure_ascii=False, indent=4)

    except FileNotFoundError:
        print(f"\nFile at {out_path} not found!")
        sys.exit(1)


def write_merged_dict_to_jsonfile(out_dict: dict, out_path: str) -> None:
    """
    gets the desired output path, opens and reads any JSON data that may already be
    there, and recursively merges in param data from the most recent round of API
    calls

    :param out_dict dict[unknown]: dict of data from round of API calls to merge and
    write
    :param out_path str: path to file in fs that we want to write to

    :rtype None: writes output to file, nothing returned
    """
    json_dict = {}

    # attempt to read JSON out of output file. Will return empty dict if no
    # valid Json is found
    json_dict = read_jsonfile_into_dict(out_path)

    # recursively merge all dicts and nested dicts in both dictionaries
    dict_utils.merge_dicts_recursive(out_dict, json_dict)

    # write JSON content back to file
    write_dict_to_jsonfile(json_dict, out_path)

    print()
