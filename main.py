"""
This module provides driver functionality for running the GitHub extractor
via the Extractor class from the extractor module
"""

import argparse
from src import conf, extractor, file_io_utils, schema, metrics_calculator


def main():
    """driver function for GitHub Repo Extractor"""

    tab = " " * 4

    cfg_dict = get_user_cfg_dict()

    cfg_obj = conf.Cfg(cfg_dict, schema.cfg_schema)

    # init extractor object
    print("\nInitializing extractor...")
    gh_ext = extractor.Extractor(cfg_obj)
    print(f"{tab}Extractor initialization complete!\n")

    if gh_ext.get_cfg_val("issue_fields"):
        print("Getting issue data...")
        gh_ext.get_issues_data()
        print(f"{tab}Issue data complete!\n")

    else:
        print("No issue fields given! Proceeding...\n")

    if gh_ext.get_cfg_val("social_metrics_fields"):
        print("Producing social metrics...")
        metrics_calculator.get_social_metrics_data(cfg_obj)
        print(f"{tab}Social metrics complete!\n")

    else:
        print("No social metrics fields given! Proceeding...\n")

    print("Extraction complete!\n")


def get_cli_args() -> str:
    """
    get initializing arguments from CLI

    :rtype str: path to file with arguments to program
    """

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Gathers and stores specific data from GitHub repositories",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_cfg_file",
        help="Path to configuration file for the extractor",
    )

    return arg_parser.parse_args().extractor_cfg_file


def get_user_cfg_dict() -> dict:
    """
    TODO:

    :return:
    :rtype:
    """
    cfg_path = get_cli_args()

    return file_io_utils.read_jsonfile_into_dict(cfg_path)


if __name__ == "__main__":
    main()
