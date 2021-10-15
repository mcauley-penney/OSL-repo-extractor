# Author: MP


import os


# constants
TIME_FRMT   = "%D, %I:%M:%S %p"

# constants
NL          = "\n"

ERR_MSG     = " Error: "
EXCEPT_MSG  = NL + " Exception: "

getter = NL + "Getting "
reader = NL + "Reading "
writer = NL + "Writing "

LOG_DICT = {
            "COLLATE"       : NL + "collating lists...",
            "COMPLETE"      : "Complete!",
            "F_COMMIT"      : NL + "filtering commits...",
            "F_MORE_COMMIT" : NL + "filtering commits...",
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

            "INVAL_ROW"     : NL + "row_quant config value is invalid!",
            "NO_AUTH"       : """
    Authorization file not found!
    Continuing without authentification...""",

            "R_CFG_DONE"    : NL + "Configuration read and logging initialized",
            "R_JSON_ALL"    : reader + "collated data JSON...",
            "R_JSON_COMMIT" : reader + "commit data JSON...",
            "R_JSON_ISSUE"  : reader + "issue data JSON...",
            "R_JSON_PR"     : reader + "pull request data JSON...",
            "SLEEP"         : NL + "Rate Limit imposed. Sleeping...",
            "SUCCESS"       : " Success! ",
            "V_AUTH"        : NL + "Validating user authentification...",
            "V_ROW_#_ISSUE" : NL + "Validating row quantity config for issue data collection...",
            "V_ROW_#_PR"    : NL + "Validating row quantity config for pull request data collection...",
            "W_CSV_COMMIT"  : writer + "\"commit\" type CSV...",
            "W_CSV_PR"      : writer + "\"PR\" type CSV...",
            "W_JSON_ALL"    : writer + "master list of data to JSON...",
            "W_JSON_COMMIT" : writer + "list of commit data to JSON...",
            "W_JSON_ISSUE"  : writer + "list of issue data to JSON...",
            "W_JSON_PR"     : writer + "list of PR data to JSON...",
            "PROG_START"    : "\n Attempting program start... ",
            }


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
