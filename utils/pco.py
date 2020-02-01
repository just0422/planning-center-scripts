import logging
import math
import os
import phonenumbers
import pypco
import requests
import streetaddress


pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )

parser = streetaddress.StreetAddressParser()

logger = logging.getLogger()


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
        where_queries[f"search_name_or_email_or_phone_number{i}"] = email
        i += 1

    # Gather phones to look for
    for phone in person.phones:
        where_queries[f"search_name_or_email_or_phone_number{i}"] = phone
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
    logger.debug(f"Building template for {person_f1.full_name()}")
    template = {
        'last_name': person_f1.last_name,
        'gender': person_f1.gender[0],
    }

    # Add a 'given name' if someone has a "goes by name"
    if len(person_f1.goes_by_name) > 0:
        template['first_name'] = person_f1.goes_by_name
        template['given_name'] = person_f1.first_name
    else:
        template['first_name'] = person_f1.first_name

    # Add a B-day if it exists
    if person_f1.get_dob_yyyy_mm_dd_format() != '':
        template['birthdate'] = person_f1.get_dob_yyyy_mm_dd_format()

    # Set a new person as inactive
    if person_pco:
        template['status'] = 'active'
    else:
        template['status'] = 'inactive'

    # Setup the payload with the build templat
    payload = pco.template('Person', template)

    person = None
    if person_pco:
        logger.warning(f"Creating {person_f1.full_name()}")
        person = pco.post('/people/v2/people', payload)
    else:
        logger.warning(f"Updating {person_f1.full_name()}")
        person = pco.patch('/people/v2/people/{person_pco["data"]["id"]}', payload)
        # self.set_inactive(person)

    # Extract ID and pass it to each detail function
    id = person['data']['id']
    person_exists = person_pco is None

    logging.info("Adding phone numbers")
    for phone in person_f1.phones:
        add_phone_number(id, phone, person_exists)

    logging.info("Adding emails")
    for email in person_f1.emails:
        add_email(id, email, person_exists)

    logging.info("Adding addresses")
    for address in person_f1.addresses:
        add_address(id, address, person_exists)


def add_phone_number(id, phone_f1, person_exists):
    if not phone_f1 or len(phone_f1) == 0:
        return

    # Parse the phone numbers
    phone_f1_fmt = phonenumbers.parse(phone_f1, "US")

    if person_exists:
        # Get phone numbers from PCO
        for phone in pco.iterate(f'/people/v2/people/{id}/phone_numbers'):
            # Parse the phone number
            phone_fmt = phonenumbers['data']['attributes']['number'].parse(phone, "US")

            # if any phone numbers match, return
            if phone_fmt == phone_f1_fmt:
                return

    # If it reached here, the phone number doesn't exist
    # Build a template for creation
    payload = pco.template(
        "PhoneNumber",
        {
            "number": phone_f1
        }
    )

    # Send the request
    return pco.post(f'/people/v2/people/{id}/phone_numbers', payload)


def add_email(id, email_f1, person_exists):
    if not email_f1 or len(email_f1) == 0:
        return

    if person_exists:
        # Get a list of all emails
        for email in pco.iterate(f'/people/v2/people/{id}/emails'):
            # if any match, return
            if email['data']['attributes']['address'] == email_f1:
                return

    # If it reached here, the email doesn't exist
    # Build the request
    payload = pco.template(
        "Email",
        {
            'address': email_f1
        }
    )

    # Add a new email
    return pco.post(f'/people/v2/people/{id}/emails', payload)


def add_address(id, address_f1, person_exists):
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

        # Get all addresses from planning center
        for address in pco.iterate(f'/people/v2/people/{id}/addresses'):
            address = address['data']['attributes']

            # Build geocode URL for each addres
            params_pco = {
                "benchmark": "Public_AR_Current",
                "format": "json",
                "street": address["street"],
                "city": address["city"],
                "state": address["state"],
                "zip": address["zip"]
            }

            # Send the request
            address_pco_data = requests.get(url=url, params=params_pco)

            # Compare all addresses to each other. If within X miles, return
            if compare_addresses(address_f1_data, address_pco_data):
                return

    # If it reached here, the address doesn't exist
    # Parse the planning center address and create a template
    payload = pco.template(
        "Address",
        {
            'street': address_f1['address1'] + " " + address_f1['address2'],
            'city': address_f1['city'],
            'state': address_f1['state'],
            'zip': address_f1['zip']
        }
    )

    # Add the new address to planning center
    return pco.post(f'/people/v2/people/{id}/addresses', payload)


def compare_addresses(self, addrs_f1, addrs_pco):
    radius = 6371  # km

    for addr_f1 in addrs_f1['result']['addressMatches']:
        lat_f1 = addr_f1['coordinates']['x']
        lng_f1 = addr_f1['coordinates']['y']
        for addr_pco in addrs_pco['result']['addressMatches']:
            lat_pco = addr_pco['coordinates']['x']
            lng_pco = addr_pco['coordanates']['y']

            dlat = math.radians(lat_pco - lat_f1)
            dlon = math.radians(lng_pco - lng_f1)

            a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat_f1)) * math.cos(math.radians(lat_pco)) * math.sin(dlon / 2) * math.sin(dlon / 2)

            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = radius * c

            if (distance < 100):
                return True

    return False
