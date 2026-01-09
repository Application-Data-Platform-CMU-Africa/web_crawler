import json
import re
from typing import Any
from storage.LinkModel import Link

from storage.sql_db import Database
# Untilities
# You can add anything you want

# Validate a list of numbers


def is_valid_list(lst):
    if not isinstance(lst, list):
        return False

    for item in lst:
        if not isinstance(item, int):
            return False
        if isinstance(item, bool):
            return False

    return True


# This class acts like a middleware for the spider
# It processes the data by removing pages without titles and by seting the title as the description in case there is no description
# Can add other functionalities
class DataProcessor:
    def __init__(self, data) -> None:
        self.data = data
        self.nomalize_text()

    # Function used to strip strings and set desc=title if the desc is empty

    def nomalize_text(self):
        self.data["name"] = self.data["name"].strip()
        if self.data["description"] is not None:
            self.data["description"] = self.data["description"].strip()
        else:
            self.data["description"] = self.data["name"].strip()

    # Used to check if the datast has a null title for further decisions
    def has_null_title(self):
        if self.data["name"] == None:
            return True
        else:
            return False


# This is a class in charge of storing the collected data in a DB or Just JSON
class SpiderStore:
    def __init__(self, data, db: Database, CONFIGS, TEST=True) -> None:
        self.db = db
        self.CONFIGS = CONFIGS
        self.pr_data = DataProcessor(data)
        self.TEST = TEST
        if self.pr_data.has_null_title():
            # Bcz there is not tile for this page, we are not considering
            self.is_valid = False
        else:
            self.is_valid = True
            # Strip the text and set the description=title if there is no description
            # processed_data.nomalize_text()
            self.data = self.pr_data.data
            # Create a Link object to get the hashvalue
            self.link = Link(
                data=self.data.get('data'),
                category=self.data.get('category'),
                description=self.data.get('description'),
                name=self.data.get('name'),
                organization=self.data.get('organization'),
                tags=self.data.get('tags')
            )

    def store_records(self):
        # If we are only testing, no need to store the records in an SQL db

        if self.TEST is True:
            pass
        else:
            self._store_in_sqldb()

        # Save the data to a JSON file for quick visualization and testing in case TEST is True
        with open(f'{self.CONFIGS["file_name"]}.json', 'a') as f:
            json.dump(self.data, f)
            f.write(',\n')

    # This is private
    def _store_in_sqldb(self):

        # If the link was recorded in the db before, skip it
        if self.db.check_if_exist(self.link.hash_value):
            pass
        else:
            self.db.add_link(self.link.data,
                             self.link.name,
                             self.link.hash_value,
                             self.link.description,
                             self.link.type,
                             self.link.organization,
                             self.link.tags,
                             self.link.isPrivate,
                             self.link.category)


# Custom printer
def cprint(text):
    print(f":> {text}")
