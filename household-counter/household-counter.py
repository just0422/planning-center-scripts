import enlighten
import os
import pypco
import requests
import time

from dateutil.relativedelta import relativedelta
from datetime import date

LARGE_FAMILY_SIZE=7
MINIMUM_ADULT_AGE=16

pco = pypco.PCO(
        os.environ["PCO_KEY"],
        os.environ["PCO_SECRET"]
    )

# Collect the number of people in PCO
response = pco.get('https://api.planningcenteronline.com/people/v2/people?where[status]=active&per_page=0')
people = response['meta']['total_count']

print(f"There are {people} active profiles in PCO People\n")

url = "https://api.planningcenteronline.com/people/v2/households?include=people"
response = pco.get(url)
household_total = response['meta']['total_count']

# Setup Progress Bar
manager = enlighten.get_manager()
progress = manager.counter(total=household_total, desc='Retrieving from PCO', unit='households')

# Loop through households
household_counts = {}
household_total = 0
while True:
    # Get the next 25 households
    response = pco.get(url)

    for household in response['data']:
        active = False
        household_member_count = 0
        # Check each household person to make sure someone is active
        for household_person in household['relationships']['people']['data']:
            for person in response['included']:
                # Ensure that SOMEONE in the household is active
                if person['id'] == household_person['id'] and person['attributes']['status'] == 'active':
                    active = True
                    # keep a running total of all active household members
                    household_total += 1

                # Check that the person's age is greateer than MINIMUM_ADULT_AGE
                if person['id'] == household_person['id']:
                    if person['attributes']['birthdate'] != None:
                        age = relativedelta(date.today(), date.fromisoformat(person['attributes']['birthdate'])).years

                        if age < MINIMUM_ADULT_AGE:
                            continue
                    # Age Appropriate Counter
                    household_member_count += 1

        # If a household is deemed active, record it's size
        if active:
            if household_member_count not in household_counts:
                household_counts[household_member_count] = 0
            household_counts[household_member_count] += 1
                
            """
            # If the family is large, print a link for verification
            if household_member_count >= LARGE_FAMILY_SIZE:
                primary_url = 'https://people.planningcenteronline.com/people/AC'
                id_number = household['relationships']['primary_contact']['data']['id']
                print(f"Large household ({household_member_count}) - {primary_url}{id_number}")
            """
        progress.update()

    if 'next' not in response['links']:
        break

    # On to the next set of households
    url = response['links']['next']

# Print out the results (and grab a running total of people over the MINIMUM_ADULT_AGE)
adult_total = 0
for count in range(max(household_counts.keys())):
    if count in household_counts:
        print(f"There are {household_counts[count]} households with {count} people over the age of {MINIMUM_ADULT_AGE}")

        adult_total += int(count) * household_counts[count]

print(f"\nThere are {adult_total} active people in households over the age of {MINIMUM_ADULT_AGE}")
print(f"There are {household_total} active people in households")
