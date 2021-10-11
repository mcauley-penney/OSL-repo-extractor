# Author: MP

# TODO
#   Leverage keyerrors in cfg member assignment to log errors?


# modules
import argparse


class cfg:

    def __init__( self ) -> None:
        """ init cfg object for extractor object to hold onto and reference """

        # get file name
        self.__get_CLI_args();

        # get rest of config data
        self.__extract_cfg()


    def __extract_cfg( self ) -> None:
        """ read cfg file out into obj members """

        try:
            conffile_obj = open( self.file, 'r' )

        except FileNotFoundError:
            print( "\nConfiguration file not found!" )

        else:
            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            # clean cfg
            strip_list = [ line.strip() for line in confinfo_list
                                if '-' not in line ]

            split_list = [ line.split( '=' ) for line in strip_list
                                if line != '' ]

            cfg_dict = { key.strip( ' ' ): value.strip( ' ' )
                            for ( key, value ) in split_list }

            # assign cfg items to self
            self.auth       = cfg_dict['auth_file']
            self.comm_json  = cfg_dict['commit_json']
            self.diag       = cfg_dict['diagnostics']
            self.issue_json = cfg_dict['issue_json']
            self.log_path   = cfg_dict['log']
            self.mast_json  = cfg_dict['master_json']
            self.pr_json    = cfg_dict['pr_json']
            self.repo       = cfg_dict['repo']
            self.rows       = cfg_dict['rows']

            conffile_obj.close()


    def __get_CLI_args( self ) -> None:

        # establish positional argument capability
        arg_parser = argparse.ArgumentParser( description="OSL Repo mining script" )

        # add repo input CLI arg
        arg_parser.add_argument( 'config_file', type=str, help="config file name" )

        # retrieve positional arguments
        self.file = arg_parser.parse_args().config_file


