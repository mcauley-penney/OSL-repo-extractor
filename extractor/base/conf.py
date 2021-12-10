"""TODO:"""

import logging
import sys


# XXX this works but will be annoying to maintain. Filter the user inputs some other way
PR_KEYS = ["body", "closed", "title", "userlogin", "username"]
ISSUES_KEYS = []


class Cfg:
    """
    The Cfg class provides an object which holds all of the configuration
    for the extractor class
    """

    def __init__(self, cfg_path: str) -> None:
        """
        initialize an object to hold configuration values for the extractor

        :param cfg_file str: path name to a configuration file
        :param logger obj: logger obj from ExtractorLogger class
        :raises KeyError: if a val in cfg dict is left empty
        :rtype None: initializes Cfg obj
        """
        self.__logger = logging.getLogger(__name__)
        self.__logger.info("initializing cfg...\n")

        try:
            # attempt to extract data from the cfg file
            self.cfg_dict = self.__extract_cfg(cfg_path)

        # if the cfg file is missing any fields
        except KeyError as key:
            # send an error message to the log
            missing_key_msg = f"\nMissing configuration for {key}\n"
            self.__logger.exception(missing_key_msg)

        else:
            # loop through all configuration object members and check if any is empty
            for key, val in vars(self).items():
                if val == "":
                    # if any item is empty, report it
                    missing_val_msg = (
                        f"\nERROR: cfg key {key} has no associated value. "
                        + "Please check your configuartion."
                    )

                    self.__logger.critical(missing_val_msg)

    def __extract_cfg(self, cfg_path: str) -> dict[str, str]:
        """
        open the provided configuartion file and read its contents out into a
        dictionary

        :param cfg_file str: path name to a configuration file
        :rtype None: initializes object members
        """

        def __clean_data_pt_fields(dict_to_clean: dict) -> dict:
            """
            TODO: description

            :param dict_to_clean dict: [TODO:description]
            :rtype dict: [TODO:description]
            """

            # for "fields" cfgs, split and turn into list
            for key, val in dict_to_clean.items():
                if "fields" in key:
                    if "," in val:
                        dict_to_clean[key] = val.split(",")

                    else:
                        dict_to_clean[key] = [val]

            # filter lists to remove anything not in the list of data pt keys
            dict_to_clean["pr_fields"] = [
                val for val in dict_to_clean["pr_fields"] if val in PR_KEYS
            ]

            dict_to_clean["issues_fields"] = [
                val for val in dict_to_clean["issues_fields"] if val in ISSUES_KEYS
            ]

            return dict_to_clean

        try:
            conffile_obj = open(cfg_path, encoding="UTF-8")

        except FileNotFoundError:
            self.__logger.exception("\nConfiguration file not found!")
            sys.exit(1)

        else:
            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            conffile_obj.close()

            # if line does not start with a dash, strip of whitespace and newline chars
            strip_list = [
                line.replace(" ", "").strip()
                for line in confinfo_list
                if not line.startswith("-")
            ]

            # if line is not empty, split it at assignment operator
            cfg_dict = dict([line.split("=") for line in strip_list if line])

            cfg_dict = __clean_data_pt_fields(cfg_dict)

        return cfg_dict

    def get_cfg_val(self, key: str) -> str:
        """
        print the associated value of key param

        Possible args:
            "auth_file", "commit_json", "diagnostics", "issue_fields",
            "issue_json", "functionality", "master_json", "pr_json",
            "repo", "rows"

        :param key str: associated key for desired val; defaults
        to returning the path to the config file
        """

        return self.cfg_dict[key]
