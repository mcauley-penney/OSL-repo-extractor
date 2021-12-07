"""TODO:"""

import os


# constants
TIME_FRMT = "%D, %I:%M:%S %p"

# constants
NL = "\n"

ERR_MSG = " Error: "
EXCEPT_MSG = NL + " Exception: "

GETTER = NL + "Getting "
READER = NL + "Reading "
WRITER = NL + "Writing "

LOG_DICT = {
    "COLLATE": NL + "collating lists...",
    "COMPLETE": "Complete!",
    "F_COMMIT": NL + "filtering commits...",
    "F_MORE_COMMIT": NL + "filtering commits...",
    "G_DATA_COMMIT": GETTER + "commit data...",
    "G_DATA_ISSUE": GETTER + "issue data...",
    "G_DATA_PR": GETTER + "pull request data...",
    "G_MORE_COMMIT": GETTER + "more commit data...",
    "G_MORE_ISSUE": GETTER + "more issue data...",
    "G_MORE_PAGES": GETTER + "more paginated lists...",
    "G_MORE_PR": GETTER + "more pull request data...",
    "G_PAGED_ISSUES": GETTER + "paginated list of issues...",
    "G_PAGED_PR": GETTER + "paginated list of pull requests...",
    "INVAL_TOKEN": """Invalid personal access token found!""",
    "INVAL_ROW": NL + "row_quant config value is invalid!",
    "NO_AUTH": """
    Authorization file not found!
    Please provide a valid file. Exiting...""",
    "R_CFG_DONE": NL + "Configuration read and logging initialized",
    "R_JSON_ALL": READER + "collated data JSON...",
    "R_JSON_COMMIT": READER + "commit data JSON...",
    "R_JSON_ISSUE": READER + "issue data JSON...",
    "R_JSON_PR": READER + "pull request data JSON...",
    "SLEEP": NL + "Rate Limit imposed. Sleeping...",
    "SUCCESS": " Success! ",
    "V_AUTH": NL + "Validating user authentification...",
    "V_ROW_#_ISSUE": NL + "Validating row quantity config for issue data collection...",
    "V_ROW_#_PR": NL
    + "Validating row quantity config for pull request data collection...",
    "W_CSV_COMMIT": WRITER + '"commit" type CSV...',
    "W_CSV_PR": WRITER + '"PR" type CSV...',
    "W_JSON_ALL": WRITER + "master list of data to JSON...",
    "W_JSON_COMMIT": WRITER + "list of commit data to JSON...",
    "W_JSON_ISSUE": WRITER + "list of issue data to JSON...",
    "W_JSON_PR": WRITER + "list of PR data to JSON...",
    "PROG_START": "\n Attempting program start... ",
}


def verify_dirs(file_path):
    """
    verifies that the path to parameter exists or creates that path

    :param file_path str: file path to check or create
    """

    # get only the last item in the file path, i.e. the item after the last slash
    # ( the file name )
    stripped_path_list = file_path.rsplit("/", 1)

    # determine if the split performed above created two separate items. If not
    # ( meaning the list length is 1 ), only a file name was given and that file
    # would be created in the same directory as the extractor. If the length is
    # greater than 1, we will have to either create or verify the existence of
    # the path to the file being created
    if len(stripped_path_list) > 1:

        path = stripped_path_list[0]

        os.makedirs(path, exist_ok=True)
