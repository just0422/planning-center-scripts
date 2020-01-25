import pypco
import os


pco = pypco.PCO(
        os.environ("PCO_KEY"),
        os.environ("PCO_SECRET")
    )


def find_person(person):
    # These go out with every request as a baseline for finding a person
    base_where = {
        "first_name": person.first_name,
        "last_name": person.last_name
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
        # Build where params
        where = base_where
        where[key[:-1]] = value

        # Send the request out
        possible_people = pco.people.people.list(where=where)

        # Continue of no one returns
        if len(possible_people) == 0:
            continue

        # Add someone if no one exists
        for person in possible_people:
            if person not in people_gathered:
                people_gathered.append(person)

    if len(people_gathered) != 1:
        return None

    return people_gathered[0]


def create_new_person(person_f1):
    new_person = pco.new(pypco.models.people.Person)

    new_person.first_name = person_f1.first_name
    new_person.last_name = person_f1.last_name
    new_person.
