"""
This module provides driver functionality for running the GitHub extractor via the
Extractor class from the extractor module
"""

import argparse
from v2 import extractor


def main():
    """driver function for GitHub Extractor"""

    cfg_path = get_cli_args()

    # init extractor object
    print("\nBeginning extractor init, instantiating cfg...")
    gh_ext = extractor.Extractor(cfg_path)

    if gh_ext.get_cfg_val("issues_fields"):
        print("\nGetting issue data...")
        gh_ext.get_issues_data()
        print("\nIssue data complete!")

    else:
        print("\nNo issue fields given! Proceeding...")

    if gh_ext.get_cfg_val("pr_fields"):
        print("\nGetting pull request data...")
        gh_ext.get_pr_data()
        print("\nPull request data complete!")

    else:
        print("\nNo pull request fields given!")

    print("\nExtraction complete!")


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
