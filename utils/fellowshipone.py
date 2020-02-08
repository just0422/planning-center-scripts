import json
import logging
import string
import os
import sys

from datetime import datetime
from .pyf1 import F1API

logger = logging.getLogger()
logging.SUCCESS = 25

f1 = F1API(
        clientKey=os.environ["F1_KEY_P"],
        clientSecret=os.environ["F1_SECRET_P"],
        username=os.environ["F1_USER"],
        password=os.environ["F1_PASS"]
    )


class PersonF1:
    """Representation of a person from FellowshipOne"""
    def __init__(self, person):
        self.error = False
        self.id = person[0]
        self.household_id = person[1]

        self.first_name = ""
        self.last_name = ""
        self.last_updated = datetime(2000, 1, 1)

        self.emails = []
        self.phones = []
        self.addresses = []

        if not self.get_details(self.id):
            logger.info(f"Empty details for {self.id}")
            self.error = True
            return
        self.get_communications(self.id)
        self.get_addresses(self.id)

        logger.success(f"Retrieved {self.full_name()}")

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_details(self, person_id):
        logger.debug("Getting Details")
        # Get person from F1
        response = f1.get(f"/v1/People/{person_id}.json")
        if not response:
            logger.error(f"Error retrieving details from {person_id}")
            return False

        # Decode the request
        person = response.content.decode('utf8')
        person = json.loads(person)
        person = person["person"]

        logger.debug(person)

        self.first_name = (person["firstName"] or '').capitalize()
        self.middle_name = (person["middleName"] or '').capitalize()
        self.last_name = (person["lastName"] or '').capitalize()
        self.goes_by_name = (person["goesByName"] or '').capitalize()
        self.gender = person["gender"]
        self.dob = person["dateOfBirth"]
        self.status = person["status"]["name"]
        if person["maritalStatus"] in ["Married", "Single", "Widowed"]:
            self.marital_status = person["maritalStatus"]

        if person["lastUpdatedDate"]:
            self.last_updated = datetime.strptime(person["lastUpdatedDate"], '%Y-%m-%dT%H:%M:%S')
        return True

    def get_communications(self, person_id):
        logger.debug("Getting Communications")
        # Get communications from F1
        response = f1.get(f"/v1/People/{person_id}/Communications.json")
        if not response:
            logger.error(f"Error retrieving {self.full_name}'s communications")
            return

        # Decode the request
        communications = response.content.decode('utf8')
        communications = json.loads(communications)

        logger.debug(communications)

        # Check for validity
        if not communications or "communications" not in communications:
            return

        if not communications["communications"] or "communication" not in communications["communications"]:
            return

        # Pull out the array
        communicationsArr = communications["communications"]["communication"]

        # Add each communication
        for communication in communicationsArr:
            communication_gen_type = communication["communicationGeneralType"]
            communication_value = communication["communicationValue"]
            communication_type = communication["communicationType"]["name"]

            if communication_gen_type == "Telephone":
                self.phones.append({
                    "number": communication_value,
                    "type": communication_type
                })
            if communication_gen_type in ["Email", "Home Email"]:
                self.emails.append({
                    "email": communication_value,
                    "type": communication_type
                })

    def get_addresses(self, person_id):
        logger.debug("Getting Addresses")
        # Get Addresses from F1
        response = f1.get(f"/v1/People/{person_id}/Addresses.json")
        if not response:
            logger.error(f"Error retrieving {self.full_name}'s addresses")
            return

        # Decode the request
        addresses = response.content.decode('utf8')
        addresses = json.loads(addresses)

        # Check for validity
        if not addresses or "addresses" not in addresses:
            return

        if not addresses["addresses"] or "address" not in addresses["addresses"]:
            return

        # Pull out the array
        addressesArr = addresses["addresses"]["address"]

        logger.debug(addresses)

        # Add each address
        for address in addressesArr:
            address_obj = {}

            address_obj["address1"] = address["address1"] or ''
            address_obj["address2"] = address["address2"] or ''
            address_obj["city"] = address["city"] or ''
            address_obj["zip"] = address["postalCode"] or ''
            address_obj["state"] = address["stProvince"] or ''

            self.addresses.append(address_obj)

    def get_attributes(self):
        response = f1.get("/v1/People/{self.id}/Attributes.json")
        response.raise_for_status()

        attributes = response.content
        attributes = attributes.decode('utf8')
        attributes = json.loads(attributes)

        # Check for validity
        if not attributes or "attributes" not in attributes:
            return

        if not attributes["attributes"] or "attribute" not in attributes["attributes"]:
            return
        return attributes["attirbutes"]["attribute"]

    def has_a_bad_name(self):
        return (self.is_a_bad_word(self.first_name) or
                self.is_a_bad_word(self.last_name))

    def is_a_bad_word(self, word):
        invalid_chars = string.punctuation
        invalid_chars = invalid_chars.replace(".", "")
        invalid_chars = invalid_chars.replace("(", "")
        invalid_chars = invalid_chars.replace(")", "")
        return (
            len(word.replace(".", "")) <= 1 or
            word.count('.') >= 2 or
            word[0] in '(.' or
            word[len(word) - 1] == ')' or
            any(char.isdigit() for char in word) or
            any(char in set(invalid_chars) for char in word) or
            len(word.split(' ')) > 3 or
            ' and ' in word
        )

    def has_no_contact_information(self):
        return len(self.emails) == 0 and len(self.phones) == 0

    def get_dob_yyyy_mm_dd_format(self):
        if not self.dob or len(self.dob) == 0:
            return '1900-01-01'

        dob = datetime.strptime(self.dob, '%m/%d/%y')
        return dob.strftime('%Y-%m-%d')

    def profile_is_too_old(self, limit):
        return self.last_updated < limit
