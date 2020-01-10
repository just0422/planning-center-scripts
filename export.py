#!/usr/local/bin/python3
import sqlite3
import string
import sys

from sqlite3 import Error

from dateutil.relativedelta import relativedelta
import datetime


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("Connected to " + db_file)
    except Error as e:
        print(e)

    return conn


def compare(first, second):
    return (
        first and second and
        len(first) > 0 and len(second) > 0 and
        first.lower() == second.lower()
    )


def is_a_duplicate(row, rows, index):
    # row without UIDs
    first_name = row[4]
    last_name = row[3]
    dob = row[8]
    address1 = row[10]
    address2 = row[11]
    pref_phone = row[12]
    mobile_phone = row[13]
    pref_email = row[14]
    email = row[15]

    for check_row in rows[index - 20: index + 20]:
        if row == check_row:
            return False

        cr_first_name = check_row[4]
        cr_last_name = check_row[3]
        cr_dob = check_row[8]
        cr_address1 = check_row[10]
        cr_address2 = check_row[11]
        cr_pref_phone = check_row[12]
        cr_mobile_phone = check_row[13]
        cr_pref_email = check_row[14]
        cr_email = check_row[15]

        # Skip if the name is different
        if first_name != cr_first_name:
            continue
        if last_name != cr_last_name:
            continue

        # Check DOB, address, email, or mobile_phone
        if (compare(dob, cr_dob) or
                compare(address1, cr_address1) or
                compare(address2, cr_address2) or
                compare(mobile_phone, cr_mobile_phone) or
                compare(pref_phone, cr_pref_phone) or
                compare(email, cr_email) or
                compare(pref_email, cr_pref_email)):
            return True

    return False


def is_a_bad_word(word):
    invalid_chars = string.punctuation
    invalid_chars = invalid_chars.replace(".", "")
    invalid_chars = invalid_chars.replace("(", "")
    invalid_chars = invalid_chars.replace(")", "")
    return (
        len(word.replace(".", "")) <= 1 or
        word.count('.') >= 2 or
        word[0] == '(' or
        word[len(word) - 1] == ')' or
        any(char.isdigit() for char in word) or
        any(char in set(invalid_chars) for char in word) or
        len(word.split(' ')) > 3
    )


if __name__ == '__main__':
    try:
        conn = create_connection("data_files/normal.db")

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people")

        rows = cursor.fetchall()

        print(len(rows))

        valid = 0
        lap = 0
        dups = 0
        lasts = 0
        firsts = 0

        kids = 0

        for row in rows[1:]:
            lap += 1
            sys.stdout.write('\rProfile Count: {0}'.format(lap))
            sys.stdout.flush()

            first_name = row[4].strip()
            last_name = row[3].strip()

            if is_a_bad_word(first_name):
                # print(row)
                firsts += 1
                continue

            if is_a_bad_word(last_name):
                # print(row)
                lasts += 1
                continue

            if is_a_duplicate(row, rows, lap):
                # print(row)
                dups += 1
                continue

            valid += 1

        print('\n\n')
        print("Valid profiles: " + str(valid))
        print("Duplicates: " + str(dups))
        print("Bad First names: " + str(firsts))
        print("Bad Last Names: " + str(lasts))
    finally:
        if conn:
            conn.close()
