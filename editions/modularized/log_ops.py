#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 


from . import cfg
from . import os_ops
import logging


#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def complete( logger ):

    log_and_print( "COMPLETE", "INFO", logger )  




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def init_logger( log_file_name ):

    log_msg_format  = "\n%(asctime)s: %(message)s"
    log_time_format = "%a, " + cfg.TIME_FRMT

    # create logger
    logger = logging.getLogger( __name__ )

    # create file handling
    os_ops.verify_dirs( log_file_name )
    out_file_handler = logging.FileHandler( log_file_name )

    # create formatting
    formatter = logging.Formatter( log_msg_format, log_time_format )
    out_file_handler.setFormatter( formatter )

    # set log level
    logger.setLevel( logging.INFO )

    # set handler
    logger.addHandler( out_file_handler )


    return logger 
         



#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def log_and_print( msg_format, log_type, logger ):

    nl_tab = cfg.NL_TAB

    getter = nl_tab + "Getting "
    reader = nl_tab + "Reading "
    writer = nl_tab + "Writing "

    str_dict = {
            "COLLATE"       : nl_tab + " Collating lists...",
            "COMPLETE"      : " Complete! ",
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
""",
            "INVAL_ROW"     : nl_tab + "row_quant config value is invalid!",
            "R_JSON_ALL"    : reader + "collated data JSON...",
            "R_JSON_COMMIT" : reader + "commit data JSON...",
            "R_JSON_ISSUE"  : reader + "issue data JSON...",
            "R_JSON_PR"     : reader + "pull request data JSON...",
            "SLEEP"         : nl_tab + "Rate Limit imposed. Sleeping...",
            "W_CSV_COMMIT"  : writer + "\"commit\" type CSV...",
            "W_CSV_PR"      : writer + "\"PR\" type CSV...",
            "W_JSON_COMMIT" : writer + "list of commit data to JSON...",
            "W_JSON_ISSUE"  : writer + "list of issue data to JSON...",
            "W_JSON_ALL"    : writer + "master list of data to JSON...",
            "W_JSON_PR"     : writer + "list of PR data to JSON...",
            "PROG_START"    : "\nAttempting program start...",
            }


    out_msg = str_dict[msg_format]

    if log_type == "INFO":
        logger.info( out_msg )

        if msg_format != "COMPLETE" and msg_format != "PROG_START":
            out_msg = cfg.INFO_MSG + out_msg

    elif log_type == "ERROR":
        logger.error( out_msg )
        out_msg = cfg.ERR_MSG + out_msg 

    elif log_type == "EXCEPT":
        logger.exception( out_msg )
        out_msg = cfg.EXCEPT_MSG + out_msg 
        

    if msg_format == "COMPLETE":
        out_msg = nl_tab + cfg.TAB + cfg.BKGRN + out_msg + cfg.TXTRST + '\n'


    print( out_msg ) 
 
