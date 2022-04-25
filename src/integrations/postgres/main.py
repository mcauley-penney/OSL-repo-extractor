"""
TODO:

Documentation: https://www.psycopg.org/docs/
"""

import psycopg2


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
    cur = conn.cursor()

    num_list = []

    for item_type in ["pr", "pr_issue"]:
        cur = select(cur, item_type, "*")
        query_res = cur.fetchall()

        for data_tuple in query_res:
            num_list.append(int(data_tuple[0]))

        sorted_num_list = sorted(num_list)
        write_output("pt_keys.txt", sorted_num_list)

    # conn.commit()

    close_cnxn(cur, conn)


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


def insert(cursor, table, cols_list, val_list):
    """TODO:"""

    # joining in this manner turns a python list of strings into one string in
    # the format that SQL expects of a list of columns, e.g.
    # ["col1", "col2"] ─►  "col1, col2"
    col_str = ", ".join(cols_list)

    # cursor.execute(f"INSERT INTO {table}({col_str}) VALUES {*val_list,};")
    cursor.execute(f"INSERT INTO {table}({col_str}) VALUES %s")(val_list)


def select(cursor, table, col):
    """TODO:"""

    cursor.execute(f"SELECT {col} from {table};")

    return cursor


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
