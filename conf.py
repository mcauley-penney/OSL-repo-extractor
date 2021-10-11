# Author: MP

# TODO create separate logging class to hold logging functionality

# modules
import logging
import utils


class cfg:

    def __init__( self ) -> None:
        """ init cfg object for extractor object to hold onto and reference """

        # get file name
        self.file       = utils.get_CLI_args();

        # init members
        self.auth       = ""
        self.comm_json  = None
        self.diag       = False
        self.issue_json = None
        self.log        = ""
        self.logger     = None
        self.mast_json  = None
        self.PAT        = ""
        self.pr_json    = None
        self.repo       = None
        self.rows       = None


    def extract_cfg( self ) -> None:
        """ read cfg file out into obj members """


        def init_logger( self ) -> None:
            """ initialize logger and assign to cfg object """

            log_msg_format  = "\n%(asctime)s: %(message)s"
            log_time_format = "%a, " + utils.TIME_FRMT

            # create logger
            logger = logging.getLogger( __name__ )

            # create file handling
            utils.verify_dirs( self.log )
            out_file_handler = logging.FileHandler( self.log )

            # create formatting
            formatter = logging.Formatter( log_msg_format, log_time_format )
            out_file_handler.setFormatter( formatter )

            # set log level
            logger.setLevel( logging.INFO )

            # set handler
            logger.addHandler( out_file_handler )


            self.logger = logger


        def read_auth( self ):
            """ read personal access token out of auth file """

            try:
                authfile_obj = open( self.auth, 'r' )

            except FileNotFoundError:
                # print error
                # OLD: log_and_print( "NO_AUTH", "ERROR", logger )
                print( "There is no auth file at" + self.auth + "!\n" )

            else:
                # read contents out of auth file object
                # this should be one line with a personal accss token ( PAT )
                authinfo_line = authfile_obj.readline()

                # remove newline chars and surrounding whitespace from PAT
                self.auth = authinfo_line.strip().strip( '\n' )

                authfile_obj.close()


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
            self.log        = cfg_dict['log']
            self.logger     = init_logger( self.log )
            self.mast_json  = cfg_dict['master_json']
            self.PAT        = read_auth( self.auth )
            self.pr_json    = cfg_dict['pr_json']
            self.repo       = cfg_dict['repo']
            self.rows       = cfg_dict['rows']


            conffile_obj.close()
