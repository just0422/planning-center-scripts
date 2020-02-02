#!/usr/local/bin/python3
import argparse
import logging
import sys
import sqlite3
import utils.pco as pco

from sqlite3 import Error
from utils.fellowshipone import PersonF1
from utils.rainbow_logger import RainbowLoggingHandler


parser = argparse.ArgumentParser()
parser.add_argument("-d", dest="debug", action="store_true")


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


def compareArrays(first, second):
    same = False
    for f in first:
        for s in second:
            if compare(f, s):
                same = True
    return same


def is_a_duplicate(person, rows, index):
    for check_row in rows[index - 20: index + 20]:
        check_person = PersonF1(check_row)
        if person.id == check_person.id:
            logger.error("Found Her")
            return False

        # Skip if the name is different
        if person.first_name != check_person.first_name:
            continue
        if person.last_name != check_person.last_name:
            continue

        # Check DOB, address, email, or mobile_phone
        if (compare(person.dob, check_person.dob) or
                compareArrays(person.addresses, check_person.addresses) or
                compareArrays(person.phones, check_person.phones) or
                compareArrays(person.emails, check_person.emails)):
            return True

    return False


if __name__ == '__main__':
    logger = logging.getLogger()

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Log Pretty Output to the terminal
    handler = RainbowLoggingHandler(sys.stdout)
    formatter = logging.Formatter(
                    "[%(asctime)s] - %(levelname)s - "
                    "%(filename)s:%(funcName)s:%(lineno)d --- "
                    "%(message)s"
                )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Log simple output to file
    file_handler = logging.FileHandler("output.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    try:
        # Connect to the database
        conn = create_connection("data_files/test.db")

        # Query the DB
        logging.info("Pulling data from database")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people")
        people = cursor.fetchall()

        # Setup counters for metrics
        valid = 0
        lap = 0
        dups = 0
        names = 0

        # Gather Mapping for Attributes
        cursor.execute("SELECT * FROM field_mapping")
        field_mappings = cursor.fetchall()

        # Organize Mappings
        attributes_to_fields = {}
        for field in field_mappings:
            attributes_to_fields[field[0]] = field

        # Iterate over results
        for person in people:
            # Objectify the person
            person_f1 = PersonF1(person)

            lap += 1
            logging.info('Profile Count: {0}'.format(lap))

            # Check for a bad first or last name
            if person_f1.has_a_bad_name():
                names += 1
                logging.warning(f"{person_f1.full_name()} has a bad name")
                continue

            # Check for a duplicate
            if is_a_duplicate(person_f1, people, lap):
                dups += 1
                logging.warning(f"{person_f1.full_name()} is a duplicate")
                continue

            # If it reach here, the person's profile is valid
            valid += 1
            logging.info(f"{person_f1.full_name()} is valid")

            # Attempt to find the person in Planning Center
            #   (Returns none if they don't exist)
            person_pco = pco.find_person(person_f1)

            # Sending person to Planning Center
            logging.info(f"Sending '{person_f1.full_name()}' to Planning Center")
            person_pco = pco.send_person_to_pco(person_f1, person_pco)

            logging.info(f"Retrieving {person_f1.first_name}'s attributes from FellowshipOne")
            # Get attributes from FellowshipOne
            attributes = person_f1.get_attributes()

            logging.info(f"Sending {person_f1.first_name}'s attributes to Planning Center")
            # Send each attribute to Planning Center
            for attribute in attributes:
                f1_attribute_id = attribute['@id']

                if f1_attribute_id in attributes_to_fields.keys():
                    pco.send_attribute(person_pco['id'], f1_attribute_id, attribute, attributes_to_fields[f1_attribute_id])

        logging.info('\n\n')
        logging.info("Valid profiles: " + str(valid))
        logging.info("Duplicates: " + str(dups))
        logging.info("Bad Names: " + str(names))
        # logging.info("Bad Last Names: " + str(lasts))
    finally:
        if conn:
            conn.close()
