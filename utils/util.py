import json
import re
from typing import Any

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
        self.data["name"] =  self.data["name"].strip()
        if self.data["description"] is not None: 
            self.data["description"] =  self.data["description"].strip()
        else:
            self.data["description"] = self.data["name"].strip()

    # Used to check if the datast has a null title for further decisions 
    def has_null_title(self):
        if self.data["name"] == None:
            return True
        else:
            return False
    


# Custom printer 
def cprint(text):
    print(f":> {text}")



