#!/usr/local/bin/python3
import argparse
import csv
import datetime
import enlighten
import logging
import sys
import sqlite3
import time
import utils.pco as pco

from sqlite3 import Error
from utils.fellowshipone import PersonF1
from utils.rainbow_logger import RainbowLoggingHandler


parser = argparse.ArgumentParser()
parser.add_argument("-d", dest="debug", action="store_true")

logger = logging.getLogger()


def main():

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logging.SUCCESS = 25
    logging.addLevelName(logging.SUCCESS, 'SUCCESS')
    setattr(logger, 'success', lambda message, *args: logger._log(logging.SUCCESS, message, args))

    # Log Pretty Output to the terminal
    handler = RainbowLoggingHandler(sys.stdout)
    formatter = logging.Formatter(
                    "[%(asctime)s] - %(levelname)s - "
                    "%(module)s:%(funcName)s:%(lineno)d --- "
                    "%(message)s"
                )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Log simple output to file
    file_handler = logging.FileHandler("output.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create an output file for each type of data
    people_csv = open('out_files/people.csv', mode='w')
    people_csv_writer = csv.writer(people_csv, delimiter=',')
    contacts_csv = open('out_files/contacts.csv', mode='w')
    contacts_csv_writer = csv.writer(contacts_csv, delimiter=',')
    addresses_csv = open('out_files/addresses.csv', mode='w')
    addresses_csv_writer = csv.writer(addresses_csv, delimiter=',')
    attributes_csv = open('out_files/attributes.csv', mode='w')
    attributes_csv_writer = csv.writer(attributes_csv, delimiter=',')

    csv_writers = [people_csv_writer, contacts_csv_writer, addresses_csv_writer, attributes_csv_writer]

    try:
        # Connect to the database
        conn = create_connection("data_files/normal.db")

        # Query the DB
        logger.info("Pulling data from database")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people")
        people = cursor.fetchall()

        # Setup Progress bar
        manager = enlighten.get_manager()
        get_progress = manager.counter(total=len(people[999:1003]), desc='Getting from F1', unit='people', color="yellow")

        # Gather Mapping for Attributes
        cursor.execute("SELECT * FROM field_mapping")
        field_mappings = cursor.fetchall()

        # Organize Mappings
        attributes_to_fields = {}
        for field in field_mappings:
            attributes_to_fields[field[0]] = field

        people_f1 = []
        # Iterate over results
        for person in people[999:1003]:
            # Objectify the person
            people_f1.append(PersonF1(person, csv_writers))
            get_progress.update()

        # Setup progress bars
        send_progress = manager.counter(total=len(people_f1), desc='Sending to PCO', unit='people', color="red")
        # Setup counters for metrics
        lap = 0
        valid = manager.counter(desc='|- Valid Profiles -', unit='people')
        dups = manager.counter(desc='|- Duplicates -----', unit='people')
        names = manager.counter(desc='|- Bad Names ------', unit='people')
        empty = manager.counter(desc='|- Empty Profiles -', unit='people')
        old = manager.counter(desc='|- Old Profiles ---', unit='people')
        error = manager.counter(desc='|- Errors ---------', unit='people')

        limit = datetime.datetime(2009, 1, 1)
        # Iterate over results
        for person_f1 in people_f1:
            time.sleep(0.01)
            logger.success("-" * 100)
            lap += 1

            send_progress.update()

            # Check to see if an error occured on retrieval
            if person_f1.error:
                logger.warning(f"Profile {person_f1.id} had errors")
                error.update()
                continue

            # Check for a bad first or last name
            if person_f1.has_a_bad_name():
                logger.warning(f"{person_f1.full_name()} has a bad name")
                names.update()
                continue

            # Check for existing contact information
            if person_f1.has_no_contact_information():
                logger.warning(f"{person_f1.full_name()} has no contact information")
                empty.update()
                continue

            # Check to see if the profile is too old
            if person_f1.profile_is_too_old(limit):
                logger.warning(f"{person_f1.full_name()} is too old")
                old.update()
                continue

            # Check for a duplicate
            if is_a_duplicate(person_f1, people_f1, lap):
                logger.warning(f"{person_f1.full_name()} is a duplicate")
                dups.update()
                continue

            # If it reach here, the person's profile is valid
            logger.success(f"{person_f1.full_name()} is valid")
            valid.update()

            # Attempt to find the person in Planning Center
            #   (Returns none if they don't exist)
            logger.info(f"Looking for '{person_f1.full_name()} in FellowshipOne")
            person_pco = pco.find_person(person_f1)

            if person_pco:
                # Sending person to Planning Center
                logger.info(f"Sending '{person_f1.full_name()}' to Planning Center")
                person_pco = pco.send_person_to_pco(person_f1, person_pco)
                logger.success(f"Sent {person_f1.full_name()} to Planning Center")

                logger.info(f"Retrieving {person_f1.first_name}'s attributes from FellowshipOne")
                # Get attributes from FellowshipOne
                attributes = person_f1.get_attributes(csv_writers[3])

                logger.info(f"Sending {person_f1.first_name}'s attributes to Planning Center")

                # Send each attribute to Planning Center
                for attribute in attributes:
                    f1_attribute_id = int(attribute['attributeGroup']['attribute']['@id'])

                    if f1_attribute_id in attributes_to_fields.keys():
                        pco.send_attribute(person_pco, f1_attribute_id, attribute, attributes_to_fields[f1_attribute_id])
                logger.success(f"Sent {person_f1.first_name}'s attributes to Planning Center")
            else:
                # Skip people who don't exist
                if not person_f1.gender:
                    pronoun = 'This person'
                elif 'f' in person_f1.gender[0].lower():
                    pronoun = 'She'
                else:
                    pronoun = 'He'
                logger.error(f"Skipping {person_f1.full_name()} -- {pronoun} does not exist in Planning Center")
    finally:
        if conn:
            conn.close()


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info("Connected to " + db_file)
    except Error as e:
        logger.error(e)

    return conn


def compare(first, second):
    logger.debug(first)
    logger.debug(second)
    return (
        first and second and
        isinstance(first, str) and isinstance(second, str) and
        len(first) > 0 and len(second) > 0 and
        first.lower() == second.lower()
    )


def compareArrayOfDicts(firstArr, secondArr):
    for first in firstArr:
        for second in secondArr:
            for key in first.keys():
                if key not in second.keys():
                    continue
                if key in ['city', 'state', 'zip', 'type']:
                    continue

                if compare(first[key], second[key]):
                    return True
    return False


def is_a_duplicate(person, people, index):
    check_people = []
    low = (lambda x: x if x >= 0 else 0)(index - 20)
    high = (lambda x: x if x <= len(people) else len(people))(index + 20)
    for i in range(low, high):
        check_people.append(people[i])

    for check_person in check_people:
        if person.id == check_person.id:
            return False

        # Skip if the name is different
        if person.first_name != check_person.first_name:
            continue
        if person.last_name != check_person.last_name:
            continue

        # Check DOB, address, email, or mobile_phone
        if (compare(person.dob, check_person.dob) or
                compareArrayOfDicts(person.addresses, check_person.addresses) or
                compareArrayOfDicts(person.phones, check_person.phones) or
                compareArrayOfDicts(person.emails, check_person.emails)):
            return True

    return False


if __name__ == '__main__':
    main()
