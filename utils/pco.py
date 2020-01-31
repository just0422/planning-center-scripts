import phonenumbers
import pypco
import requests
import streetaddress
import os


pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )

parser = streetaddress.StreetAddressParser()


def find_person(person):
    # These go out with every request as a baseline for finding a person
    base_where = {
        "where[first_name]": person.first_name,
        "where[last_name]": person.last_name
    }

    # Each of these entries, paired with the baseline info should be unique and
    #  adequate for checking if someone already exists in PCO
    where_queries = {
        "birthdate ": person.get_dob_yyyy_mm_dd_format(),
        "search_name_or_email_or_phone_numberl": person.pref_phone,
        "search_name_or_email_or_phone_number2": person.mobile_phone,
        "search_name_or_email_or_phone_number3": person.pref_email,
        "search_name_or_email_or_phone_number4": person.email
    }

    people_gathered = []
    for key, value in where_queries.items():
        if len(value) == 0:
            continue

        # Build where params
        where = base_where
        where[f"where[{key[:-1]}]"] = value

        # Send the request out
        possible_people = pco.iterate('/people/v2/people', **where)

        # Add someone if no one exists
        for person in possible_people:
            if person not in people_gathered:
                people_gathered.append(person)

    if len(people_gathered) != 1:
        return None

    return people_gathered[0]

def send_person_to_pco(person_f1, person_pco):
    template = {
        'first_name': person_f1.first_name,
        'last_name': person_f1.last_name
    }

    if person_f1.get_dob_yyyy_mm_dd_format() != '':
        template['birthdate'] = person_f1.get_dob_yyyy_mm_dd_format()

    payload = pco.template('Person', template)

    person = None
    if person_pco:
        person = pco.post('/people/v2/people', payload)
    else:
        person = pco.patch('/people/v2/people/{person_pco["data"]["id"]}', payload)
        # self.set_inactive(person)
    
    # Extract ID and pass it to each detail function
    id = person['data']['id']
    person_exists = person_pco != None

    self.add_phone_number(id, person_f1.pref_phone, person_exists)
    self.add_phone_number(id, person_f1.mobile_phone, person_exists)

    self.add_email(id, person_f1.email, person_exists)
    self.add_email(id, person_f1.pref_email, person_exists)

    self.add_address(id, person_f1.address1, person_exists)
    self.add_address(id, person_f1.address2, person_exists)

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
    resp = pco.post(f'/people/v2/people/{id}/phone_numbers', payload)

def add_email(id, email_f1, person_exists):
    if not email_f1 or len(email_f1) == 0:
        return

    email_exists = False

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
    resp = pco.post(f'/people/v2/people/{id}/emails', payload)

def add_address(id, address_f1, person_exists):
    if not address_f1 or len(address_f1) == 0:
        return

    address_exists = False

    if person_exists:
        # Build US Gov geo code URL
        url_f1 = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        params_f1 = {
            "address": address_f1,
            "benchmark": "Public_AR_Current",
            "format": "json"
        }

        # Send request
        address_f1_data = requests.get(url=url_f1, params=params_f1)

        # Get all addresses from planning center
        for address in pco.iterate(f'/people/v2/people/{id}/addresses'):
            address = address['data']['attributes']

            # Build geocode URL for each addres
            url_pco = "https://geocoding.geo.census.gov/geocoder/locations/address"
            params_pco = {
                "benchmark": "Public_AR_Current",
                "format": "json",
                "street": address["street"],
                "city": address["city"],
                "state": address["state"],
                "zip": address["zip"]
            }
           
            # Send the request
            address_pco_data = requets.get(url=url_pco, params=params_pco)

            # Compare all addresses to each other. If within X miles, return

    # If it reached here, the address doesn't exist
    # Parse the planning center address and create a template
    parsed_address = parser.parse(address_f1)
    payload = pco.template(
        "Address",
        {
            'street': parsed_address['house'] + " " + parsed_address['street_full'],
            'city': parsed_address['city'],
            'state': parsed_address['state'],
            'zip': parsed_address['zip']
        }
    )
    
    # Add the new address to planning center
    resp = pco.post(f'/people/v2/people/{id}/addresses', payload)
