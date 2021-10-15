# Author: MP


import logging
import sys
import utils


class ext_log:
    # intro: ext_log ( extractor logger ) is a class that provides
    # logging functionality for extractor objects


    def __init__(self, cfg_path ) -> None:
        # initialize logger and assign to cfg object

        log_file = cfg_path.split( '/' )[1]

        log_file_name = log_file.split( '.' )[0]

        log_path = "log_files/" + log_file_name + "_log.txt"


        # make sure that log file path is there or created
        utils.verify_dirs( log_path )

        # init formats
        log_msg_format  = "\n%(asctime)s\n%(levelname)s:\n%(message)s\n"
        log_time_format = "%a, " + utils.TIME_FRMT

        # create logger
        logger = logging.getLogger( __name__ )

        # set log level
        logger.setLevel( logging.INFO )

        # establish logging to file functionality
        file_handler = logging.FileHandler( log_path )

        # create formatting obj and set format
        formatter = logging.Formatter( log_msg_format, log_time_format )
        file_handler.setFormatter( formatter )

        # set handlers for writing to file and to stdout
        logger.addHandler( file_handler )
        logger.addHandler( logging.StreamHandler( sys.stdout ))

        # init members
        self.log_path = log_path
        self.log_obj  = logger


    # logging wrappers
    def log_complete( self ):

        self.log_obj.info( "COMPLETE\n" )


    def log( self, msg, lvl="INFO" ):

        if lvl == "INFO":
            self.log_obj.log( 20, msg )

        elif lvl == "WARN":
            self.log_obj.log( 30, msg )

        elif lvl == "ERR":
            self.log_obj.log( 40, msg )

        elif lvl == "CRIT":
            self.log_obj.log( 50, msg )

        elif lvl == "EXCEPT":
            self.log_obj.exception( msg )


    def log_success( self ):

        self.log_obj.info( "SUCCESS\n" )



