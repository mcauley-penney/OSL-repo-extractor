# Author: MP


import argparse
import os

# constants
TIME_FRMT   = "%D, %I:%M:%S %p"


def get_CLI_args():

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="OSL Repo mining script" )

    # add repo input CLI arg
    arg_parser.add_argument( 'config_file', type=str, help="config file name" )

    # retrieve positional arguments
    config_filename = arg_parser.parse_args().config_file

    return config_filename


def verify_dirs( file_path ):

    # get only the last item in the file path, i.e. the item after the last
    # slash ( the file name )
    stripped_path_list = file_path.rsplit( '/', 1 )

    # the code below allows us to determine if the split performed above
    # created two separate items. If not ( meaning the list length is 1 ),
    # only a file name was given and that file would be created in the same
    # directory as the extractor. If the length is greater than 1, we will
    # have to either create or verify the existence of the path to the file
    # being created
    path_list_len = len( stripped_path_list )

    if path_list_len > 1:

        path = stripped_path_list[0]

        os.makedirs( path, exist_ok=True )
