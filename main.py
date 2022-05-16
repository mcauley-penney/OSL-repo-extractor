"""Provides driver functionality for running the GitHub extractor."""

import argparse
from src import conf, schema
from src.extractor import github_extractor
from src.utils import file_io_utils


def main():
    """Driver function for GitHub Repo Extractor."""
    tab: str = " " * 4

    cfg_dict: dict = get_user_cfg_dict()

    cfg_obj = conf.Cfg(cfg_dict, schema.cfg_schema)

    # init extractor object
    print("\nInitializing extractor...")
    gh_ext = github_extractor.Extractor(cfg_obj)
    print(f"{tab}Extractor initialization complete!\n")

    if gh_ext.get_cfg_val("issue_fields"):
        print("Getting issue data...")
        gh_ext.get_issues_data()
        print(f"{tab}Issue data complete!\n")

    else:
        print("No issue fields given!\n")

    print("Extraction complete!\n")


def get_cli_args() -> str:
    """
    Get initializing arguments from CLI.

    :return: path to file with arguments to program
    :rtype: str
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
    Get path to and read from configuration file.

    :return: dict of configuration values
    :rtype: dict
    """
    cfg_path = get_cli_args()

    return file_io_utils.read_jsonfile_into_dict(cfg_path)


if __name__ == "__main__":
    main()
