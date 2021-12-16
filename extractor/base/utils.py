"""TODO:"""


# TODO: can incorporate both of these into the extractor?


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
