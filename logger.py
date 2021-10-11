# Author: MP


import logging
import utils

NL_TAB      = "\n\t"

ERR_MSG     = " Error: "
EXCEPT_MSG  = NL_TAB + " Exception: "
INFO_MSG    = NL_TAB + " Info: "

getter = NL_TAB + "Getting "
reader = NL_TAB + "Reading "
writer = NL_TAB + "Writing "

log_dict = {
            "COLLATE"       : NL_TAB + "collating lists...",
            "COMPLETE"      : " Complete! ",
            "F_COMMIT"      : NL_TAB + "filtering commits...",
            "F_MORE_COMMIT" : NL_TAB + "filtering commits...",
            "G_DATA_COMMIT" : getter + "commit data...",
            "G_DATA_ISSUE"  : getter + "issue data...",
            "G_DATA_PR"     : getter + "pull request data...",
            "G_MORE_COMMIT" : getter + "more commit data...",
            "G_MORE_ISSUE"  : getter + "more issue data...",
            "G_MORE_PAGES"  : getter + "more paginated lists...",
            "G_MORE_PR"     : getter + "more pull request data...",
            "G_PAGED_ISSUES": getter + "paginated list of issues...",
            "G_PAGED_PR"    : getter + "paginated list of pull requests...",
            "INVAL_TOKEN"   : """
    Invalid personal access token!
    Please see https://github.com/settings/tokens
    to create a token with \"repo\" permissions!
    Continuing without authentification...""",

            "INVAL_ROW"     : NL_TAB + "row_quant config value is invalid!",
            "NO_AUTH"       : """
    Authorization file not found!
    Continuing without authentification...""",

            "R_CFG_DONE"    : NL_TAB + "Read configuration and initialize logging...",
            "R_JSON_ALL"    : reader + "collated data JSON...",
            "R_JSON_COMMIT" : reader + "commit data JSON...",
            "R_JSON_ISSUE"  : reader + "issue data JSON...",
            "R_JSON_PR"     : reader + "pull request data JSON...",
            "SLEEP"         : NL_TAB + "Rate Limit imposed. Sleeping...",
            "SUCCESS"       : " Success! ",
            "V_AUTH"        : NL_TAB + "Validating user authentification...",
            "V_ROW_#_ISSUE" : NL_TAB + "Validating row quantity config for issue data collection...",
            "V_ROW_#_PR"    : NL_TAB + "Validating row quantity config for pull request data collection...",
            "W_CSV_COMMIT"  : writer + "\"commit\" type CSV...",
            "W_CSV_PR"      : writer + "\"PR\" type CSV...",
            "W_JSON_ALL"    : writer + "master list of data to JSON...",
            "W_JSON_COMMIT" : writer + "list of commit data to JSON...",
            "W_JSON_ISSUE"  : writer + "list of issue data to JSON...",
            "W_JSON_PR"     : writer + "list of PR data to JSON...",
            "PROG_START"    : "\n Attempting program start... ",
            }


class ext_log:

    def __init__(self, log_str ) -> None:
        " initialize logger and assign to cfg object """

        log_msg_format  = "\n%(asctime)s: %(message)s"
        log_time_format = "%a, " + utils.TIME_FRMT

        # create logger
        logger = logging.getLogger( __name__ )

        # create file handling
        utils.verify_dirs( log_str )
        out_file_handler = logging.FileHandler( log_str )

        # create formatting
        formatter = logging.Formatter( log_msg_format, log_time_format )
        out_file_handler.setFormatter( formatter )

        # set log level
        logger.setLevel( logging.INFO )

        # set handler
        logger.addHandler( out_file_handler )

        # init members
        self.log_path = log_str
        self.log_obj = logger


    def exe_log( self, log_type, msg_format ) -> None:

        # generate the message to output
        out_msg = log_dict[msg_format]

        if log_type == "INFO":
            self.log_obj.info( out_msg )

            if msg_format not in { "COMPLETE", "PROG_START", "SUCCESS" } :
                out_msg = INFO_MSG + out_msg

            else:
                if msg_format == "COMPLETE":
                    out_msg = NL_TAB + '\t' + out_msg + '\n'

                elif msg_format == "SUCCESS":
                    out_msg = "\n\n" + out_msg


        elif log_type == "ERROR":
            self.log_obj.error( out_msg )
            out_msg = '\n' + ERR_MSG + out_msg

        elif log_type == "EXCEPT":
            self.log_obj.exception( out_msg )

            if out_msg != "SLEEP":
                out_msg = EXCEPT_MSG + out_msg


        print( out_msg )
