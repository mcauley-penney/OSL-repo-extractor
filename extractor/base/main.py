"""
This module provides driver functionality for running the GitHub extractor via the
Extractor class from the extractor module
"""

import argparse
import sys
import logging
from base import extractor


def main():
    """driver function for GitHub Extractor"""

    (cfg_path, log_dest) = get_cli_args()

    # create root logger
    root_logger = init_root_logger(log_dest)

    # init extractor object
    root_logger.info("Instantiating extractor...\n")
    gh_ext = extractor.Extractor(cfg_path)
    root_logger.info("Complete!\n")

    # root_logger.info("Getting issue data...\n")
    # gh_ext.get_issues_data()
    # root_logger.info("Complete!\n")

    root_logger.info("Getting PR and commit data...\n")
    gh_ext.get_pr_data()
    root_logger.info("\nComplete!\n")


def init_root_logger(log_dest):
    """
    initialize the root logger for this execution. It's configuration will
    be inherited by child loggers

    see https://stackoverflow.com/a/50755200

    :param log_dest str: file path to write logging to
    """

    log_msg_format = "[%(name)s]: %(asctime)s\n%(levelname)s:\n%(message)s\n"
    log_time_format = "%Y-%m-%d %H:%M:%S %a"

    # providing no params to getLogger() instantiates this
    # logger as root. If we provided __name__, the name would
    # be this module. We want root for now
    logger = logging.getLogger()

    # set threshhold log level
    logger.setLevel(logging.INFO)

    # establish logging to file functionality
    file_handler = logging.FileHandler(log_dest)

    # create formatting obj and set format
    formatter = logging.Formatter(log_msg_format, log_time_format)
    file_handler.setFormatter(formatter)

    # set handlers for writing to file and to stdout
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    return logger


def get_cli_args() -> tuple[str, str]:
    """
    get initializing arguments from CLI

    :rtype tuple[str, str]: file with arguments to program, destination
    to log execution run information to
    """

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Gathers and stores specific data from GitHub repositories",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_cfg_file",
        help="Path to file with settings for the extractor",
    )
    arg_parser.add_argument(
        "logging_destination",
        nargs="?",
        default="../../data/output/extractor_log.txt",
        help="Path to log messages to",
    )

    cfg_file = arg_parser.parse_args().extractor_cfg_file
    log_dest = arg_parser.parse_args().logging_destination

    # retrieve positional arguments
    return (cfg_file, log_dest)


if __name__ == "__main__":
    main()
