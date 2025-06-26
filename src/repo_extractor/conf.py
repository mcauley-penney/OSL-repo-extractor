"""The conf module exposes the Cfg class."""

import sys
import cerberus


class Cfg:
    """Object which holds all of the configuration for the extractor class."""

    def __init__(self, cfg_dict: dict, cfg_schema: dict) -> None:
        """
        Initialize an object to hold configuration values for the extractor.

        Args:
            cfg_dict (dict): configuration values provided
                by user as arg.
            cfg_schema (dict): template used to evaluate
                validity of user cfg.

        Attributes:
            cfg_dict (dict): configuration values provided
                by user as arg.
            cfg_schema (dict): template used to evaluate
                validity of user cfg.
        """
        # init object members
        self.cfg_dict = cfg_dict
        self.cfg_schema = cfg_schema

        # validate user-provided configuration dict
        self.__validate_dict_entries()

    def get_cfg_val(self, key: str):
        """
        Return the value mapped to the given key in the configuration dict.

        Args:
            key (str): associated key for desired val.

        Returns:
            list|int|str: value in the top level of the cfg
            dict associated with the given key
        """
        return self.cfg_dict[key]

    def set_cfg_val(self, key: str, val) -> None:
        """
        Set a value inside of the configuration dict.

        Args:
            key (str): the key of the dict entry to modify.
            val (): value to assign to dict[key].
        """
        self.cfg_dict[key] = val

    def __validate_dict_entries(self) -> None:
        """
        Validate given configuration against a schema.

        Use Cerberus to check all entries in the configuration
        dictionary for correctness of type and content. Fail
        stop is implemented if configuration does not meet schema
        specification.
        """
        # init schema for validation
        validator = cerberus.Validator(self.cfg_schema, require_all=True)

        # if dictionary from JSON does not follow rules in schema
        if not validator.validate(document=self.cfg_dict):
            # log an exception and print errors
            print(f"Validation error!\n{validator.errors}")
            sys.exit(1)
