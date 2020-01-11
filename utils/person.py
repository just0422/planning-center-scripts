import string

from datetime import datetime


class Person:
    """Representation of a person from F1 using the SQLite representation"""
    def __init__(self, obj):
        self.id = obj[0]
        self.household_id = obj[1]

        self.first_name = (obj[4] or '').strip()
        self.last_name = (obj[3] or '').strip()
        self.dob = (obj[8] or '').strip()
        self.address1 = (obj[10] or '').strip()
        self.address2 = (obj[11] or '').strip()
        self.pref_phone = (obj[12] or '').strip()
        self.mobile_phone = (obj[13] or '').strip()
        self.pref_email = (obj[14] or '').strip()
        self.email = (obj[15] or '').strip()

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
        if len(self.dob) == 0:
            return '1900-01-01'

        dob = datetime.strptime(self.dob, '%m/%d/%y')
        return dob.strftime('%Y-%m-%d')
