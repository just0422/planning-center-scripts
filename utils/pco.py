import pypco
import os


pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )


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


def create_new_person(person_f1):
    template = {
        'first_name': person_f1.first_name,
        'last_name': person_f1.last_name
    }

    if person_f1.get_dob_yyyy_mm_dd_format() != '':
        template['birthdate'] = person_f1.get_dob_yyyy_mm_dd_format()

    payload = pco.template('Person', template)
    new_person = pco.post('/people/v2/people', payload)

    self.add_new_details()

def add_new_details():

#    if person_f1.pref_phone != '':
#        new_person.
