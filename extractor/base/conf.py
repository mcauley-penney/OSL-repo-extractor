"""TODO:"""

# import argparse
import logging


class Cfg:
    """
    The Cfg class provides an object which holds all of the configuration
    for the extractor class
    """

    def __init__(self, cfg_path) -> None:
        """
        initialize an object to hold configuration values for the extractor

        :param cfg_file str: path name to a configuration file
        :param logger obj: logger obj from ExtractorLogger class
        :raises KeyError: if a val in cfg dict is left empty
        :rtype None: initializes Cfg obj
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("initializing cfg...\n")

        try:
            # attempt to extract data from the cfg file
            self.__extract_cfg(cfg_path)

        # if the cfg file is missing any fields
        except KeyError as key:
            # send an error message to the log
            missing_key_msg = f"\nMissing configuration for {key}\n"
            self.logger.exception(missing_key_msg)

        else:
            # loop through all configuration object members and check if any is empty
            for key, val in vars(self).items():
                if val == "":
                    # if any item is empty, report it
                    missing_val_msg = (
                        f"\nERROR: cfg key {key} has no associated value. "
                        + "Please check your configuartion."
                    )

                    self.logger.critical(missing_val_msg)

    def __extract_cfg(self, cfg_file) -> None:
        """
        open the provided configuartion file and read its contents out into a
        dictionary

        :param cfg_file str: path name to a configuration file
        :rtype None: initializes object members
        """

        try:
            conffile_obj = open(cfg_file, encoding="UTF-8")

        except FileNotFoundError:
            self.logger.exception("\nConfiguration file not found!")

        else:
            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            conffile_obj.close()

            # if line does not start with a dash, strip of whitespace and keep
            strip_list = [
                line.strip() for line in confinfo_list if not line.startswith("-")
            ]

            # if line is not empty, split it at assignment operator
            split_list = [line.split("=") for line in strip_list if line != ""]

            # turn sublists into entries in dictionary
            cfg_dict = {key.strip(): value.strip() for (key, value) in split_list}

            cfg_dict["cfg_path"] = cfg_file

            # TODO remove job member?
            self.auth_file_path = cfg_dict["auth_file"]
            self.commit_json = cfg_dict["commit_json"]
            self.diag_bool = cfg_dict["diagnostics"]
            self.issue_json = cfg_dict["issue_json"]
            self.job = cfg_dict["functionality"]
            self.master_json = cfg_dict["master_json"]
            self.pr_json = cfg_dict["pr_json"]
            self.repo = cfg_dict["repo"]
            self.row_quant = cfg_dict["rows"]
            self.full_cfg_text = cfg_dict

    def get_cfg_val(self, key="cfg_path"):
        """
        print the value of the key arg

        :param key str: associated key for desired val; defaults
                        to returning the path to the config file
        """

        return self.full_cfg_text[key]
