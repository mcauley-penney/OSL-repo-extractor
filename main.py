"""Provides driver functionality for running the GitHub extractor."""

import argparse
from repo_extractor import conf, schema
from repo_extractor.extractor import github_extractor
from repo_extractor.utils import file_io_utils as file_io


def main():
    """Driver function for GitHub Repo Extractor."""
    tab: str = " " * 4

    cfg_dict: dict = get_user_cfg()
    cfg_obj = conf.Cfg(cfg_dict, schema.cfg_schema)

    # init extractor object
    print("\nInitializing extractor...")
    gh_ext = github_extractor.Extractor(cfg_obj)
    print(f"{tab}Extractor initialization complete!\n")

    print("Mining repo data...")
    gh_ext.get_repo_issues_data()
    print(f"\n{tab}Issue data complete!\n")

    print("Extraction complete!\n")


def get_user_cfg() -> dict:
    """
    Get path to and read from configuration file.

    :return: dict of configuration values
    :rtype: dict
    """
    cfg_path = get_cli_args()

    return file_io.read_jsonfile_into_dict(cfg_path)


def get_cli_args() -> str:
    """
    Get initializing arguments from CLI.

    Returns:
        str: path to file with arguments to program
    """
    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Mines data from GitHub repositories",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_cfg_file",
        help="Path to JSON configuration file",
    )

    return arg_parser.parse_args().extractor_cfg_file


if __name__ == "__main__":
    main()
