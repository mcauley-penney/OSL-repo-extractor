"""
The conf module provides functionality related to configurations for the
extractor
"""

import sys
import cerberus


class Cfg:
    """
    The Cfg class provides an object which holds all of the configuration
    for the extractor class
    """

    def __init__(self, cfg_dict: dict, cfg_schema: dict) -> None:
        """
        initialize an object to hold configuration values for the extractor

        :param cfg_dict: configuration values provided by user as arg
        :type cfg_dict: dict
        :param cfg_schema: template used to evaluate validity of user cfg
        :type cfg_schema: dict
        """

        # init object members
        self.cfg_dict = cfg_dict
        self.cfg_schema = cfg_schema

        # validate user-provided configuration dict
        self.__validate_dict_entries()

    def get_cfg_val(self, key: str):
        """
        print the associated value of key param

        :param key str: associated key for desired val; defaults
        to returning the path to the config file
        """
        return self.cfg_dict[key]

    def set_cfg_val(self, key: str, val) -> None:
        """
        set a value inside of the configuration dict

        :param key str: the key of the dict entry to modify
        :param val str | int: value to assign to dict[key]
        :rtype None
        """
        self.cfg_dict[key] = val

    def __validate_dict_entries(self) -> None:
        """
        use Cerberus to check all entries in the configuration dictionary for
        correctness of type and content

        See extractor.CFG_SCHEMA for what is permitted

        :rtype None: exits program with failure code if cfg dict is incorrect
        """

        # init schema for validation
        validator = cerberus.Validator(self.cfg_schema, require_all=True)

        # if dictionary from JSON does not follow rules in schema
        if not validator.validate(document=self.cfg_dict):
            # log an exception and print errors
            print(f"Validation error!\n {validator.errors}")
            sys.exit(1)
