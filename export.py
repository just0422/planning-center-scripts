#!/usr/local/bin/python3
import pypco
import sqlite3
import sys

from sqlite3 import Error
from utils.person import Person


pco = pypco.PCO(
        "",
        ""
    )


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


def is_a_duplicate(person, rows, index):
    for check_row in rows[index - 20: index + 20]:
        if row == check_row:
            return False

        check_row_person = Person(check_row)

        # Skip if the name is different
        if person.first_name != check_row_person.first_name:
            continue
        if person.last_name != check_row_person.last_name:
            continue

        # Check DOB, address, email, or mobile_phone
        if (compare(person.dob, check_row_person.dob) or
                compare(person.address1, check_row_person.address1) or
                compare(person.address2, check_row_person.address2) or
                compare(person.mobile_phone, check_row_person.mobile_phone) or
                compare(person.pref_phone, check_row_person.pref_phone) or
                compare(person.email, check_row_person.email) or
                compare(person.pref_email, check_row_person.pref_email)):
            return True

    return False


if __name__ == '__main__':
    try:
        conn = create_connection("data_files/normal.db")

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people")

        rows = cursor.fetchall()

        valid = 0
        lap = 0
        dups = 0
        names = 0

        for row in rows[1:]:
            person = Person(row)

            lap += 1
            sys.stdout.write('\rProfile Count: {0}'.format(lap))
            sys.stdout.flush()

            if person.has_a_bad_name():
                names += 1
                continue

            if is_a_duplicate(person, rows, lap):
                dups += 1
                continue

            valid += 1

        print('\n\n')
        print("Valid profiles: " + str(valid))
        print("Duplicates: " + str(dups))
        print("Bad Names: " + str(names))
        # print("Bad Last Names: " + str(lasts))
    finally:
        if conn:
            conn.close()
