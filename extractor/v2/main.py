"""
This module provides driver functionality for running the GitHub extractor via the
Extractor class from the extractor module
"""

import argparse
from v2 import extractor


def main():
    """driver function for GitHub Extractor"""

    cfg_path = get_cli_args()

    # TODO: create conditional to determine items to get, e.g. issues or prs
    #   • potentially use list in cfg

    # init extractor object
    print("Beginning extractor init, instantiating cfg...\n")
    gh_ext = extractor.Extractor(cfg_path)

    # print("Getting issue data...\n")
    gh_ext.get_issues_data()
    # print("Complete!\n")

    # gh_ext.get_pr_data()


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


if __name__ == "__main__":
    main()
