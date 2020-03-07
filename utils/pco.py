import logging
import json
import math
import os
import phonenumbers
import pypco
import requests
import streetaddress
from datetime import datetime
pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )

parser = streetaddress.StreetAddressParser()

logger = logging.getLogger()

GLENDALE = 35350
BUSHWICK = 35349


def find_person(person):
    # These go out with every request as a baseline for finding a person
    base_where = {
        "where[first_name]": person.first_name,
        "where[last_name]": person.last_name
    }

    # Each entry added, paired with the baseline info should be unique and
    #  adequate for checking if someone already exists in PCO
    where_queries = {
        "birthdate ": person.get_dob_yyyy_mm_dd_format(),
    }

    i = 0
    # Gather emails to look for
    for email in person.emails:
        where_queries[f"search_name_or_email_or_phone_number{i}"] = email['email']
        i += 1

    # Gather phones to look for
    for phone in person.phones:
        where_queries[f"search_name_or_email_or_phone_number{i}"] = phone['number']
        i += 1

    logger.debug("Searching for people")
    people_gathered = []
    for key, value in where_queries.items():
        if len(value) == 0:
            continue

        # Build where params
        where = base_where.copy()
        where[f"where[{key[:-1]}]"] = value

        # Send the request out
        possible_people = pco.iterate('/people/v2/people', **where)

        # Add someone if no one exists
        for person in possible_people:
            if person not in people_gathered:
                people_gathered.append(person)

        # Reset the dictionary
        where.clear()

    logger.debug(f"Found {len(people_gathered)} matches")

    if len(people_gathered) != 1:
        return None

    return people_gathered[0]


def send_person_to_pco(person_f1, person_pco):
    person_exists = person_pco is not None
    logging.debug(f"{person_f1.full_name()} exists: {person_exists}")

    template = {
        'last_name': person_f1.last_name,
        'gender': person_f1.gender[0],
    }

    # Add a 'given name' if someone has a "goes by name"
    if person_f1.goes_by_name and len(person_f1.goes_by_name) > 0:
        template['first_name'] = person_f1.goes_by_name
        template['given_name'] = person_f1.first_name
    else:
        template['first_name'] = person_f1.first_name

    # Add a B-day if it exists
    if person_f1.dob and len(person_f1.dob) > 0:
        template['birthdate'] = person_f1.get_dob_yyyy_mm_dd_format()

    # Set a new person as inactive if they are new to PCO
    if person_pco and person_pco['data']['attributes']['status'] == 'active':
        template['status'] = 'active'
    else:
        template['status'] = 'inactive'

    # Set campus
    if person_f1.status in ['CTG', 'CTQ', 'CTB English', 'CTG High School', 'CTG Junior High']:
        template['primary_campus_id'] = GLENDALE
    if person_f1.status in ['CTB', 'CTB Espanol', 'CTB Junior High', 'CTB High School']:
        template['primary_campus_id'] = BUSHWICK

    logging.debug(f"Building template for {person_f1.full_name()}")
    # Setup the payload with the build templat
    payload = pco.template('Person', template)

    logging.debug(f"{person_f1.full_name()} payload: {payload}")

    try:
        person = None
        if person_exists:
            logging.warning(f"Updating {person_f1.full_name()}")
            person = pco.patch(f'/people/v2/people/{person_pco["data"]["id"]}?include=field_data', payload)
        else:
            logging.warning(f"Creating {person_f1.full_name()}")
            person = pco.post('/people/v2/people', payload)

    except Exception as e:
        logging.error(f'Status: {e.status_code}')
        logging.error(f'Message: {e.message}')
        logging.error(f'Response: {e.response_body}')

    # Extract ID and pass it to each detail function
    id = person['data']['id']

    logging.info("Sending phone numbers")
    for phone in person_f1.phones:
        send_phone_number(id, phone, person_exists)

    logging.info("Sending emails")
    for email in person_f1.emails:
        send_email(id, email, person_exists)

    logging.info("Sending addresses")
    for address in person_f1.addresses:
        send_address(id, address, person_exists)

    return person


def send_phone_number(id, phone_f1, person_exists):
    try:
        phone_type = phone_f1["type"]
        phone_f1 = phone_f1["number"]
        if not phone_f1 or len(phone_f1) == 0:
            return

        # Parse the phone numbers
        phone_f1_obj = phonenumbers.parse(phone_f1, "US")
        if person_exists:
            # Get phone numbers from PCO
            for phone in pco.iterate(f'/people/v2/people/{id}/phone_numbers'):
                # Parse the phone number
                phone = phone['data']['attributes']['number']
                phone_fmt = phonenumbers.parse(phone, "US")

                # if any phone numbers match, return
                if phone_fmt.national_number == phone_f1_obj.national_number:
                    return

        location = ""
        if phone_type.lower() in "home phone":
            location = "Home"
        if any(phone_type.lower() in phone for phone in ["mobile phone", "emergency phone"]):
            location = "Mobile"
        if phone_type.lower() in "work phone":
            location = "Work"

        # If it reached here, the phone number doesn't exist
        # Build a template for creation
        phone_f1_basic = str(phone_f1_obj.national_number)
        phone_f1_formatted = f"({phone_f1_basic[0:3]}) {phone_f1_basic[3:6]}-{phone_f1_basic[6:]}"
        template = {
            "number": phone_f1_formatted,
            "location": location
        }
        payload = pco.template('PhoneNumber', template)

        logging.info(f"Sending Phone Number: {phone_f1_formatted}")
        logging.debug(f"Phone Number payload: {payload}")
        # Send the request
        return pco.post(f'/people/v2/people/{id}/phone_numbers', payload)
    except Exception as e:
        logging.error(f'Status: {e.status_code}')
        logging.error(f'Message: {e.message}')
        logging.error(f'Response: {e.response_body}')


def send_email(id, email_f1, person_exists):
    try:
        email_type = email_f1['type']
        email_f1 = email_f1['email']
        if not email_f1 or len(email_f1) == 0:
            return

        if person_exists:
            # Get a list of all emails
            for email in pco.iterate(f'/people/v2/people/{id}/emails'):
                # if any match, return
                if email['data']['attributes']['address'].lower() == email_f1.lower():
                    return

        location = ""
        if any(email_type.lower() in email for email in ["home email", "infellowship login"]):
            location = "Home"
        if email_type.lower() in "email":
            location = "Work"
        # If it reached here, the email doesn't exist
        # Build the request
        template = {
            'address': email_f1,
            'location': location
        }
        payload = pco.template("Email", template)

        logging.info(f"Sending Email: {email_f1}")
        logging.debug(f"Email payload: {payload}")
        # Add a new email
        return pco.post(f'/people/v2/people/{id}/emails', payload)
    except Exception as e:
        logging.error(f'Status: {e.status_code}')
        logging.error(f'Message: {e.message}')
        logging.error(f'Response: {e.response_body}')


def send_address(id, address_f1, person_exists):
    try:
        if not address_f1 or len(address_f1) == 0:
            return

        if person_exists:
            # Build US Gov geo code URL
            url = "https://geocoding.geo.census.gov/geocoder/locations/address"
            params_f1 = {
                "benchmark": "Public_AR_Current",
                "format": "json",
                "street": address_f1["address1"],
                "city": address_f1["city"],
                "state": address_f1["state"],
                "zip": address_f1["zip"]
            }

            # Send request
            address_f1_data = requests.get(url=url, params=params_f1)
            address_f1_data = address_f1_data.content
            address_f1_data = address_f1_data.decode('utf8')
            address_f1_data = json.loads(address_f1_data)

            # Get all addresses from planning center
            for address in pco.iterate(f'/people/v2/people/{id}/addresses'):
                address = address['data']['attributes']

                # Build geocode URL for each address
                params_pco = {
                    "benchmark": "Public_AR_Current",
                    "format": "json",
                    "street": address["street"],
                    "city": address["city"],
                    "state": address["state"],
                    "zip": address["zip"],
                }

                # Send the request
                address_pco_data = requests.get(url=url, params=params_pco)
                address_pco_data = address_pco_data.content
                address_pco_data = address_pco_data.decode('utf8')
                address_pco_data = json.loads(address_pco_data)

                # Compare all addresses to each other. If within X miles, return
                if compare_addresses(address_f1_data, address_pco_data):
                    return

        # If it reached here, the address doesn't exist
        # Parse the planning center address and create a template
        template = {
            'street': address_f1['address1'] + " " + address_f1['address2'],
            'city': address_f1['city'],
            'state': address_f1['state'],
            'zip': address_f1['zip'],
            'location': 'home'
        }
        payload = pco.template("Address", template)

        logging.info(f"Sending Address: {address_f1['address1']} {address_f1['address2']}, {address_f1['city']}, {address_f1['state']} {address_f1['zip']}")
        logging.debug(f"Email payload: {payload}")
        # Add the new address to planning center
        return pco.post(f'/people/v2/people/{id}/addresses', payload)
    except Exception as e:
        logging.error(f'Status: {e.status_code}')
        logging.error(f'Message: {e.message}')
        logging.error(f'Response: {e.response_body}')


def compare_addresses(addrs_f1, addrs_pco):
    radius = 6371  # km

    for addr_f1 in addrs_f1['result']['addressMatches']:
        lat_f1 = addr_f1['coordinates']['x']
        lng_f1 = addr_f1['coordinates']['y']
        for addr_pco in addrs_pco['result']['addressMatches']:
            lat_pco = addr_pco['coordinates']['x']
            lng_pco = addr_pco['coordinates']['y']

            dlat = math.radians(lat_pco - lat_f1)
            dlon = math.radians(lng_pco - lng_f1)

            a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat_f1)) * math.cos(math.radians(lat_pco)) * math.sin(dlon / 2) * math.sin(dlon / 2)

            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = radius * c

            logging.debug(f"F1 Address: {addr_f1['matchedAddress']}")
            logging.debug(f"PCO Address:  {addr_pco['matchedAddress']}")
            logging.debug(f"Distance between: {distance}km")

            if (distance < 0.5):
                return True

    return False


def send_attribute(person, f1_attribute_id, attribute, mapping):
    logging.info(f"Sending attribute {attribute['attributeGroup']['attribute']['name']} to Planning Center")
    pco_type = mapping[2]
    person_id = person['data']['id']

    if pco_type == "field_data":
        value = ""
        if attribute["startDate"]:
            value = datetime.strptime(attribute["startDate"], '%Y-%m-%dT%H:%M:%S')
        else:
            value = datetime.strptime(attribute["createdDate"], '%Y-%m-%dT%H:%M:%S')

        value = value.strftime('%Y-%m-%d')
        template = {
            "value": value,
            "field_definition_id": mapping[1]
        }
        payload = pco.template("FieldDatum", template)
        logger.debug(payload)

        # See if field data exists in planning center
        field_datum_id = -1
        for field_datum in person['included']:
            if template['field_definition_id'] == int(field_datum['relationships']['field_definition']['data']['id']):
                field_datum_id = int(field_datum['id'])

        field_definition = pco.get(f'/people/v2/field_definitions/{template["field_definition_id"]}')
        if field_datum_id > 0:
            logging.info(f"Updating Custom Field - {field_definition['data']['attributes']['name']}")
            pco.patch(f'/people/v2/field_data/{field_datum_id}', payload)
        else:
            logging.info(f"Creating Custom Field - {field_definition['data']['attributes']['name']}")
            pco.post(f'/people/v2/people/{person_id}/field_data', payload)
    if pco_type == "wed_anniversary":
        value = datetime.strptime(attribute["startDate"], '%Y-%m-%dT%H:%M:%S')
        value = value.strftime('%Y-%m-%d')
        template = {
            'anniversary': value
        }

        payload = pco.template('Person', template)
        person = pco.patch(f'/people/v2/people/{person["data"]["id"]}', payload)
