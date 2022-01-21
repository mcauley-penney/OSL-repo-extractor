""" The conf package provides classes related to configurations for the extractor"""

import json
import sys
import cerberus


def _extract_cfg(cfg_path: str) -> dict:
    """
    open the provided configuartion file, which comes in JSON format, and read
    its contents out into a dictionary

    :param cfg_file str: path name to a JSON configuration file
    :rtype None: initializes object members
    """

    try:
        with open(cfg_path, encoding="UTF-8") as conffile_obj:
            cfg_text = conffile_obj.read()

    except FileNotFoundError:
        print("\nConfiguration file not found!")
        sys.exit(1)

    else:
        return json.loads(cfg_text)


class Cfg:
    """
    The Cfg class provides an object which holds all of the configuration
    for the extractor class
    """

    def __init__(self, cfg_path: str, cfg_schema) -> None:
        """
        initialize an object to hold configuration values for the extractor

        :param cfg_file str: path name to a configuration file
        :rtype None: initializes Cfg obj
        """

        print("initializing cfg...\n")

        # get dictionary of configuration values from file w/ JSON
        self.cfg_dict = _extract_cfg(cfg_path)

        # init schema for validation
        validator = cerberus.Validator(cfg_schema, require_all=True)

        # if dictionary from JSON does not follow rules in schema
        if not validator.validate(document=self.cfg_dict):
            # log an exception and print errors
            print(f"Validation error!\n {validator.errors}")
            sys.exit(1)

    def get_cfg_val(self, key: str):
        """
        print the associated value of key param

        :param key str: associated key for desired val; defaults
        to returning the path to the config file
        """

        return self.cfg_dict[key]
