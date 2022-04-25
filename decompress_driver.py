"""
TODO
"""

import argparse
from src import file_io_utils


def main():
    """driver function for compression"""

    arg_list = get_cli_args()

    for arg in arg_list:
        print(f"Decompressing {arg}...")
        file_io_utils.decompress_gzip_to_jsonfile(arg, arg.rsplit(".", 1)[0])
        print(f"{' ' * 4}Decompression complete!\n")


def get_cli_args() -> str:
    """
    get initializing arguments from CLI

    :rtype str: path to file with arguments to program
    """

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="compress files for storage",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "files_list",
        nargs="+",
        help="file names for files to compress",
    )

    return arg_parser.parse_args().files_list


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
