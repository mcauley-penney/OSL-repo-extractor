"""The io module provides I/O functionality to the Extractor class"""

import json
from json.decoder import JSONDecodeError
import sys


def read_json(cfg_path: str) -> dict:
    """
    open the provided configuartion file, which comes in JSON format, and read
    its contents out into a dictionary

    :param cfg_file str: path name to a JSON configuration file
    :rtype dict: dictionary constructed from JSON string
    """

    try:
        with open(cfg_path, encoding="UTF-8") as conffile_obj:
            cfg_text = conffile_obj.read()

    except FileNotFoundError:
        print(f"\nFile at {cfg_path} not found!")
        sys.exit(1)

    else:
        return json.loads(cfg_text)


def write_dict_to_json(out_dict: dict, out_path: str) -> None:
    """
    gets the desired output path, opens and reads any JSON data that may already be
    there, and recursively merges in param data from the most recent round of API
    calls

    :param out_dict dict[unknown]: dict of data from round of API calls to merge and
    write
    :param out_path str: path to file in fs that we want to write to

    :rtype None: writes output to file, nothing returned
    """

    def __merge_dicts(add_dict, base_dict) -> None:
        """
        loops through keys in dictionary of data from round of API calls to merge
        their data into existing JSON data

        credit Paul Durivage: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

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
                __merge_dicts(add_dict[key], base_dict[key])

            else:
                # assign the new value from the last round of calls to the existing
                # key
                base_dict[key] = add_dict[key]

    json_dict = {}

    # attempt to read JSON out of output file
    try:
        with open(out_path, "r", encoding="UTF-8") as json_outfile:
            json_dict = json.load(json_outfile)

    # if no JSON content exists there, ignore
    except JSONDecodeError:
        pass

    # in any case
    finally:
        # recursively merge all dicts and nested dicts in both dictionaries
        __merge_dicts(out_dict, json_dict)

        # write JSON content back to file
        with open(out_path, "w", encoding="UTF-8") as json_outfile:
            json.dump(json_dict, json_outfile, ensure_ascii=False, indent=4)

    print()
