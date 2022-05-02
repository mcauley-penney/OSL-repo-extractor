"""
TODO:

Documentation: https://www.psycopg.org/docs/
"""

import sys
import psycopg2

sys.path.append("../../..")
from src import file_io_utils


def main():
    """[TODO:description]"""

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="pt",
        user="postgres",
        password="postgres",
    )

    # Create a cursor object
    cur_cursor = conn.cursor()

    table = "pr_issue"

    # read keys into list
    key_file = "/home/m/files/work/GitHub-Repo-Extractor/data/extractor/output/PowerToys/PowerToys_pg_keys.txt"
    metrics_file = "/home/m/files/work/GitHub-Repo-Extractor/data/extractor/output/PowerToys/PowerToys_metrics.json"

    with open(key_file, "r", encoding="UTF-8") as key_fptr:
        key_list_str = key_fptr.read()

    key_list = key_list_str.split("\n")

    # read json data into dict
    metrics_dict = file_io_utils.read_jsonfile_into_dict(metrics_file)

    for key in key_list:
        try:
            cur_metric_dict = metrics_dict[key]

        except KeyError:
            # simply ignore
            pass

        else:
            for sub_key, val in cur_metric_dict.items():
                update(cur_cursor, table, sub_key, val, str(key))

    conn.commit()

    close_cnxn(cur_cursor, conn)


def close_cnxn(cursor, cnxn):
    """
    close postgres cursor and connection objects

    :param cursor: postgres cursor
    :type cursor:
    :param cnxn: connection to postgres db
    :type cnxn:
    """
    cursor.close()
    cnxn.close()


def insert(cursor, table, col: str, val: str) -> None:
    """TODO:"""

    insert_str = f"INSERT INTO {table}({col}) VALUES ({val});"

    cursor.execute(insert_str)


def select(cursor, table: str, col: str):
    """TODO:"""

    try:
        cursor.execute(f"SELECT {col} from {table};")

    except psycopg2.errors.UndefinedColumn:
        print(f'Error: Column "{col}" does not exist!\n')
        return []

    else:
        return cursor.fetchall()


def update(cursor, table: str, col: str, val: str, item_num: str):
    """
    TODO
    """
    update_str = f"UPDATE {table} SET {col} = {val} WHERE pr = '{item_num}';"
    cursor.execute(update_str)


def write_output(filepath, output):
    """

    :param path:
    :type path:
    :param output:
    :type output:
    """
    with open(filepath, "w", encoding="UTF-8") as file_obj:
        for line in output:
            file_obj.write(f"{line}\n")


if __name__ == "__main__":
    main()
