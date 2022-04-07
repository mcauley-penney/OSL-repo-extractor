"""TODO:"""

import argparse
import sys


sys.path.append("../..")
from src import file_io
from src.metrics import transformations

# from src.metrics import transformations


def main():
    """driver function for social metrics transformations"""

    issue_json = get_cli_args()

    issue_dict = file_io.read_json_to_dict(issue_json)

    # issue_comments = issue_dict["issue_comment"]

    for issue in issue_dict.values():

        comment_dict = issue["issue_comments"]

        discussants_set = transformations.get_unique_discussants(comment_dict)

        print(discussants_set)

        # issue_comments = issue["issue_comment"]

        # print(issue_comments)

    # transformations.get_unique_discussants(issue_dict)


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
