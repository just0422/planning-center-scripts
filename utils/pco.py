import address
import phonenumbers
import pypco
import os


pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )

parser = address.AddressParser()


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
    else
        person = pco.patch('/people/v2/people/{person_pco['data']['id']}, payload)

    self.add_new_details(person_f1, new_person)

def update_new_person(person_pco, person_f1):
    

def add_new_details(person_f1, person_pco):
    id = person_pco['data']['id']

    self.add_phone_number(id, person_f1.pref_phone)
    self.add_phone_number(id, person_f1.mobile_phone)

    self.add_email(id, person_f1.email)
    self.add_email(id, person_f1.pref_email)

    self.add_address(id, person_f1.address1)
    self.add_address(id, person_f1.address2)

def add_phone_number(id, phone_f1):
    phone_f1_fmt = phonenumbers.parse(phone_f1, "US")

    for phone in pco.iterate(f'/people/v2/people/{id}/phone_numbers'):
        phone_fmt = phonenumbers['data']['attributes']['number'].parse(phone, "US")

        if phone_fmt == phone_f1_fmt:
            return

    payload = pco.template(
        "PhoneNumber",
        {
            "number": phone_f1
        }
    )

    resp = pco.post(f'/people/v2/people/{id}/phone_numbers', payload)

def add_email(id, email_f1):
    email_exists = False

    for email in pco.iterate(f'/people/v2/people/{id}/emails'):
        if email['data']['attributes']['address'] == email_f1:
            return

    payload = pco.template(
        "Email",
        {
            'address': email_f1
        }
    )

    resp = pco.post(f'/people/v2/people/{id}/emails', payload)

self add_address(id, address_f1):
    address_f1 = parser.parse_addres(address_f1)
    address_f1_street = {0} {1} {2} {3}".format(
                                            address_f1.house_number,
                                            address_f1.street_prefix, 
                                            address_f1.street,
                                            address_f1.street_suffix
                                        )

    address_exists = False

    for address in pco.iterate(f'/people/v2/people/{id}/addresses'):
        address = address['data']['attributes']

        street = address['street'] == address_f1_street
        city = address['city'] == address_f1.city
        state = address['state'] == address_f1.state
        zip = address['zip'] == address_f1.zip

        if street and city and state and zip:
            return

    payload = pco.template(
        "Address",
        {
            'street': address_f1_street,
            'city': address_f1.city,
            'state': address_f1.state,
            'zip': address_f1.zip
        }
    )

    resp = pco.post(f'/people/v2/people/{id}/addresses', payload)
