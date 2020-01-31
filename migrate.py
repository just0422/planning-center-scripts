#!/usr/local/bin/python3
import logging
import sys
import sqlite3
import utils.pco as pco

from sqlite3 import Error
from utils.fellowshipone import PersonF1
from utils.rainbow_logger import RainbowLoggingHandler


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info("Connected to " + db_file)
    except Error as e:
        logging.error(e)

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

        check_row_person = PersonF1(check_row)

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
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = RainbowLoggingHandler(sys.stdout)
    formatter = logging.Formatter(
                    "[%(asctime)s] "
                    "%(levelname)s:%(funcName)s:%(lineno)d ---"
                    "%(message)s"
                )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    """
    logging.basicConfig(
        format="[%(asctime)s] "
               "%(levelname)s:%(funcName)s:%(lineno)d ---"
               "%(message)s",
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )
    """

    try:
        # Connect to the database
        conn = create_connection("data_files/test.db")

        # Query the DB
        logging.info("Pulling data from database")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people")
        rows = cursor.fetchall()

        # Setup counters for metrics
        valid = 0
        lap = 0
        dups = 0
        names = 0

        # Iterate over results
        for row in rows:
            # Objectify the person
            person_f1 = PersonF1(row)

            lap += 1
            logging.info('Profile Count: {0}'.format(lap))

            # Check for a bad first or last name
            if person_f1.has_a_bad_name():
                names += 1
                logging.warning(f"{person_f1.full_name()} has a bad name")
                continue

            # Check for a duplicate
            if is_a_duplicate(person_f1, rows, lap):
                dups += 1
                logging.warning(f"{person_f1.full_name()} is a duplicate")
                continue

            # If it reach here, the person's profile is valid
            valid += 1
            logging.info(f"{person_f1.full_name()} is valid")

            # Attempt to find the person in planning center
            #   (Returns none if they don't exist)
            person_pco = pco.find_person(person_f1)

            sys.exit()

            # Sending person to PCO
            logging.info("Sending {person_f1.full_name()} in Planning Center")
            pco.send_person_to_pco(person_f1, person_pco)

            # Get attributes from F1
            attributes = person_f1.get_attributes()

        logging.info('\n\n')
        logging.info("Valid profiles: " + str(valid))
        logging.info("Duplicates: " + str(dups))
        logging.info("Bad Names: " + str(names))
        # logging.info("Bad Last Names: " + str(lasts))
    finally:
        if conn:
            conn.close()
