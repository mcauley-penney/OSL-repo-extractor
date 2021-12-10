"""TODO:"""

import os


ISSUE_CMD_DICT = {
    "test": "test",
}


PR_CMD_DICT = {
    "body": lambda cur_pr: clean_str(cur_pr.body),
    "closed": lambda cur_pr: cur_pr.closed_at.strftime("%D, %I:%M:%S %p"),
    "title": lambda cur_pr: clean_str(cur_pr.title),
    "userlogin": lambda cur_pr: cur_pr.user.login,
    "username": lambda cur_pr: cur_pr.user.name,
}


# logging str dict
GET = "\nGetting "
READ = "\nReading "
WRITE = "\nWriting "

# TODO remove unneeded strs
LOG_DICT = {
    "COLLATE": "\nCollating lists...",
    "COMPLETE": "Complete!",
    "F_COMMIT": "\nFiltering commits...",
    "F_MORE_COMMIT": "\nFiltering more commits...",
    "G_DATA_COMMIT": f"{GET} commit data...",
    "G_DATA_ISSUE": f"{GET} issue data...",
    "G_DATA_PR": f"{GET} pull request data...",
    "G_MORE_COMMIT": f"{GET} more commit data...",
    "G_MORE_ISSUE": f"{GET} more issue data...",
    "G_MORE_PAGES": f"{GET} more paginated lists...",
    "G_MORE_PR": f"{GET} more pull request data...",
    "G_PAGED_ISSUES": f"{GET} paginated list of issues...",
    "G_PAGED_PR": f"{GET} paginated list of pull requests...",
    "INVAL_TOKEN": "Invalid personal access token found!",
    "INVAL_ROW": "\nrow_quant config value is invalid!",
    "NO_AUTH": """
    Authorization file not found!
    Please provide a valid file. Exiting...""",
    "R_CFG_DONE": "\nConfiguration read and logging initialized",
    "R_JSON_ALL": f"{READ} collated data JSON...",
    "R_JSON_COMMIT": f"{READ} commit data JSON...",
    "R_JSON_ISSUE": f"{READ} issue data JSON...",
    "R_JSON_PR": f"{READ} pull request data JSON...",
    "SLEEP": "\nRate Limit imposed. Sleeping...",
    "SUCCESS": " Success! ",
    "V_AUTH": "\nValidating user authentification...",
    "V_ROW_#_ISSUE": "\nValidating row quantity config for issue data collection...",
    "V_ROW_#_PR": "\nValidating row quantity config for pull request data collection...",
    "W_CSV_COMMIT": f'{WRITE} "commit" type CSV...',
    "W_CSV_PR": f'{WRITE} "PR" type CSV...',
    "W_JSON_ALL": f"{WRITE} master list of data to JSON...",
    "W_JSON_COMMIT": f"{WRITE} list of commit data to JSON...",
    "W_JSON_ISSUE": f"{WRITE} list of issue data to JSON...",
    "W_JSON_PR": f"{WRITE} list of PR data to JSON...",
    "PROG_START": "\nAttempting program start... ",
}


def check_row_quant_safety(paged_list, range_start, range_end) -> int:
    """
    validates second val of row range (end of data to collect) provided in cfg

    :param paged_list [TODO:type]: [TODO:description]
    :param range_end [TODO:type]: [TODO:description]
    :param range_start [TODO:type]: [TODO:description]
    :rtype int: [TODO:description]
    """

    safe_val = range_end

    if range_end <= range_start or paged_list.totalCount < range_end:
        safe_val = paged_list.totalCount

    return safe_val


def clean_str(str_to_clean):
    """
    If a string is empty or None, returns NaN.
    Otherwise, strip the string of any carriage
    returns and newlines

    :param str_to_clean str: string to clean and return
    """

    if str_to_clean is None or str_to_clean == "":
        return "Nan"

    output_str = str_to_clean.replace("\r", "")
    output_str = output_str.replace("\n", "")

    return output_str.strip()


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
