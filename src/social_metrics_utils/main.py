"""TODO:"""

import argparse
import sys

sys.path.append("../../..")
from src import file_io
from src.integration_utils.social_metrics import transformations

# from src.metrics import transformations


def main():
    """driver function for social metrics transformations"""

    issue_json = get_cli_args()

    issue_dict = file_io.read_json_to_dict(issue_json)

    for issue in issue_dict.values():

        if issue["num_comments"] > 0:
            comment_dict = issue["issue_comments"]

            discussants_set = transformations.get_unique_discussants(comment_dict)

            print(discussants_set)

            issue_wc = transformations.get_issue_wordiness(comment_dict)

            print(issue_wc)


def get_cli_args() -> str:
    """
    get initializing arguments from CLI

    :rtype str: path to file with arguments to program
    """

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Gather social metrics from GitHub repository data",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "repo_data_json",
        help="Path to JSON file containing data from a GitHub repository mined by the extractor",
    )

    return arg_parser.parse_args().repo_data_json


if __name__ == "__main__":
    main()
