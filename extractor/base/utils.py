"""TODO:"""

# import json
import os


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
        output_str = "Nan"

    else:
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
