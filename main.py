"""Provides driver functionality for running the GitHub extractor."""

import argparse
from repo_extractor import conf, extractor, schema, utils


def main():
    """Driver function for GitHub Repo Extractor."""
    tab: str = " " * 4

    cfg_dict: dict = get_user_cfg()
    cfg_obj = conf.Cfg(cfg_dict, schema.cfg_schema)

    print("\nInitializing extractor...")
    gh_ext = extractor.Extractor(cfg_obj)
    print(f"{tab}Extractor initialization complete!")

    print("\nRunning extractor...")
    gh_ext.get_repo_issues_data()
    print(f"{tab}Issue data complete!")

    print("\nExtraction complete!\n")


def get_user_cfg() -> dict:
    """
    Get path to and read from configuration file.

    :return: dict of configuration values
    :rtype: dict
    """
    cfg_path = get_cli_args()

    return utils.read_jsonfile_into_dict(cfg_path)


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
