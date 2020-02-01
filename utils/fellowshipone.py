import json
import logging
import string
import os

from datetime import datetime
from .pyf1 import F1API

logger = logging.getLogger()

f1 = F1API(
        clientKey=os.environ["F1_KEY_P"],
        clientSecret=os.environ["F1_SECRET_P"],
        username=os.environ["F1_USER"],
        password=os.environ["F1_PASS"]
    )


class PersonF1:
    """Representation of a person from F1 using the SQLite representation"""
    def __init__(self, obj):
        self.id = obj[0]
        self.household_id = obj[1]

        self.emails = []
        self.phones = []
        self.addresses = []

        self.get_details(self.id)
        self.get_communications(self.id)
        self.get_addresses(self.id)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
            word[0] == '(' or
            word[len(word) - 1] == ')' or
            any(char.isdigit() for char in word) or
            any(char in set(invalid_chars) for char in word) or
            len(word.split(' ')) > 3
        )

    def get_dob_yyyy_mm_dd_format(self):
        if not self.dob or len(self.dob) == 0:
            return '1900-01-01'

        dob = datetime.strptime(self.dob, '%m/%d/%y')
        return dob.strftime('%Y-%m-%d')

    def get_details(self, person_id):
        logging.debug("Getting Details")
        # Get person from F1
        response = f1.get(f"/v1/People/{person_id}.json")

        # Decode the request
        person = response.content.decode('utf8')
        person = json.loads(person)
        person = person["person"]

        self.first_name = person["firstName"]
        self.middle_name = person["middleName"]
        self.last_name = person["lastName"]
        self.goes_by_name = person["goesByName"]
        self.gender = person["gender"]
        self.dob = person["dateOfBirth"]
        self.marital_status = person["maritalStatus"]

    def get_communications(self, person_id):
        logging.debug("Getting Communications")
        # Get communications from F1
        response = f1.get(f"/v1/People/{person_id}/Communications.json")

        # Decode the request
        communications = response.content.decode('utf8')
        communications = json.loads(communications)

        # Pull out the array
        communicationsArr = communications["communications"]["communication"]

        # Add each communication
        for communication in communicationsArr:
            communication_type = communication["communicationGeneralType"]
            communication_value = communication["communicationValue"]

            if communication_type == "Telephone":
                self.phones.append(communication_value)
            if communication_type == "Email":
                self.emails.append(communication_value)

    def get_addresses(self, person_id):
        logging.debug("Getting Addresses")
        # Get Addresses from F1
        response = f1.get(f"/v1/People/{person_id}/Addresses.json")

        # Decode the request
        addresses = response.content.decode('utf8')
        addresses = json.loads(addresses)

        # Pull out the array
        addressesArr = addresses["addresses"]["address"]

        # Add each address
        for address in addressesArr:
            address_obj = {}

            address_obj["address1"] = address["address1"]
            address_obj["address2"] = address["address2"]
            address_obj["city"] = address["city"]
            address_obj["zip"] = address["postalCode"]
            address_obj["state"] = address["stProvince"]

            self.addresses.append(address_obj)

    def get_attributes(self):
        response = f1.get("/v1/People/{self.id}/Attributes.json")

        attributes = response.decode('utf8')
        attributes = json.loads(attributes)

        return attributes
