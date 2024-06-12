from http.client import HTTPException
import json
import os
import subprocess
from spiders.fetchopensouce import FetchOpenSource
from spiders.licenses import LicenceAnalyser
from utils.util import cprint


"""
To add a script / command

1. Create a class which inherit from the class Command
2. Create a constructor ex:
def __init__(self) -> None:
        # Assigning a command name
        self.COMMAND_NAME = ["opensource"]
    
3. You can create any methode you wnat but the most important is exec which ovarrides the parent methode with your executions
4. Add a documentation variable to the class created ex: DOCUMENTATION = {"key":"command", "value":"description"}
*** Under the CrawlerUCLI class ***
5. Add the command in the self.commands_level_one variable ex: self.commands_level_one = ['show', 'publish', ...]
6. Create the command ex: publish = PablishCommand() and append it to the  self.commands_list list ex:  self.commands_list = [show, crawl, publish, ...]
7. Finaly go to ShowManuel class and add the command documentation for users to be able to see it in the terminal. 
ex: soted_list = sorted([
                {"key": "clear", "value": "To clean the terminal"},
                {"key": "close", "value": "Close the program"},
                {"key": "exit", "value": "Exit from a loop or another function"},
                self.DOCUMENTATION,
                Show.DOCUMENTATION, ])
Good luck!!

"""


CONFIG_FILE_URI="./configs/config.json"
GIT_REPOS_URI="./configs/git_repos.json"

class Information():
    title = ""
    body = []
    step=0
    def __init__(self, title, body) -> None:
        self.title = title
        self.body = body
        if len(self.body) < 10:
            self.step=0
        else:
            self.step = int(len(self.body)/7)


class Command():
    COMMAND_NAME = []
    DOCUMENTATION = {}

    def exec(self, *args, **kwargs):
        cprint(f"Executing command {self.COMMAND_NAME}")

class Show(Command):
    DOCUMENTATION = {"key":"show", "value":"Dispaly lists of 'show' commands"}
    def __init__(self, info,  close, name) -> None:
        self.COMMAND_NAME = name
        self.information = info
        self.close = close

    def escaper(self, text, tabs):
        if len(text)<tabs:
            return " " * (tabs-len(text))
        return""

    def exec(self, *args, **kwargs):
        cprint("")
        cprint(f"{self.information.title}")
        cprint("")       
        c = 0
        steps = self.information.step
        # Fin the number of ecaptes
        tabs = max([len(el.get('key')) for el in self.information.body])
        number_of_elements = len(self.information.body)
        for element in self.information.body:
            c+=1
            if steps == 0:
                pass
            else:
                if (c%7 == 0):
                    cprint("Press 'ENTER' to go to the next page ('exit' to go back, close to 'close' the app)")
                    command = input(":> ")
                    if command is None:
                        pass
                    elif command == 'close':
                        self.close()
                    elif command == 'exit':
                        break

            cprint(f"{c}. {self.escaper(f'{c}', len(f'{number_of_elements}'))} {element.get('key')} {self.escaper(element.get('key'), tabs)} {element.get('value')}")


class OpenSourceFetch(Command):
    DOCUMENTATION = {"key":"opensource", "value":"To fetch repos based on a given topic"}
    
    def __init__(self) -> None:
        self.COMMAND_NAME = ["opensource"]
        
    def exec (self, *args, **kwargs):
        choice = input(":> Enter a topic: ")
        fetcher = FetchOpenSource(topic=choice)
        fetcher.crawl()
    

class OpenLicensesCollecter(Command):
    DOCUMENTATION =  {"key":"license", "value":"Crawl a list of github repot's lices file"}
    TEST = False
    SELECTED_CONF = {}
    FILE_DIR = "./data/licenses.json"
    def __init__(self) -> None:
        self.COMMAND_NAME = ["license"]
        self.CONFIG_FILE = open(GIT_REPOS_URI)
        self.CONFIGS = json.load(self.CONFIG_FILE)

    def exec (self, *args, **kwargs):

        process = LicenceAnalyser(self.CONFIGS, self.FILE_DIR)
        process.crawl()
       
                



class ShowManuel(Show):
    DOCUMENTATION = {"key": "show man", "value": "To show all available commands"}
    def __init__(self, close) -> None:
        # List of all commands documentations
        soted_list = sorted([
                {"key": "clear", "value": "To clean the terminal"},
                {"key": "close", "value": "Close the program"},
                {"key": "exit", "value": "Exit from a loop or another function"},
                self.DOCUMENTATION,
                Show.DOCUMENTATION,
                OpenLicensesCollecter.DOCUMENTATION,
                OpenSourceFetch.DOCUMENTATION
            ], key=lambda el: el['key'])
        
        info = Information(
            title="List of available commands",
            body= soted_list
        )
        super().__init__(info, close, ["show", "man"])




class CrawlerUCLI():
    command1 = None
    command2 = None
    command3 = None
    on = True
    commands = []
    c_len = 0

    INVALID_COMMAND_MESSAGE = "Note a valid command use show man to learn about the tool"

    def __init__(self) -> None:
        self.print_program_title()
        self.commands_level_one = ['show', 'crawl', 'publish', 'delete', 'exit', 'close', 'clear', 'jconfig', 'classify', 'license', 'opensource']
        self.commands_level_two = ['website', 'country', 'man', 'test', 'verify', 'db', 'file']
        info = Information(
            title="Available 'show' commands",
            body=[
                ShowManuel.DOCUMENTATION
            ]
        )
        show = Show(info=info, close=self.close, name=["show"])
        show_manuel = ShowManuel(close=self.close)
        license = OpenLicensesCollecter()
        opensource = OpenSourceFetch()
        self.commands_list = [
            show,
            show_manuel,
            license,
            opensource
        ]

    def __str__(self) -> str:
        return f"{self.command1} {self.command2} {self.command3} {self.commands} {self.c_len}"
    
    def validate_command(self, args):
        self.commands  = args.split(" ")    
        self.c_len = len(self.commands)

        if(self.c_len>3 or self.c_len==0):
            return {"code":1, "message": self.INVALID_COMMAND_MESSAGE}
        
        # check if the command submited is one of the recognized commands
        if self.commands[0] in self.commands_level_one: 
             self.command1 = self.commands[0]
        else:
            return {"code":1, "message": self.INVALID_COMMAND_MESSAGE}
        
        # check if the command submited is one of the recognized commands
        if self.c_len > 1:
            if (self.c_len == 2) or (self.c_len == 3 and self.commands[1] in self.commands_level_two):
                self.command2 = self.commands[1]
            else:
                return {"code":1, "message": self.INVALID_COMMAND_MESSAGE}
        
        # check if the command submited is one of the recognized commands
        if self.c_len == 3 :
            self.command3 = self.commands[2]  
         
        return {"code":0}
    
    def parse_args(self):
        while self.on:
            args = input(":> ")
            resp = self.validate_command(args)
            if(resp.get('code') == 0):
                self.execute_comand()
            
    
    def print_program_title(self):
        cprint("==================== OPEN DATA PORTAL CRAWL BOT ====================")
        cprint("Use 'show man' to learn the basic commands. 'close' to close the program")
        cprint("")


    def dosexec(self, args):
        subprocess.call(args,  shell=True)

    def clear(self):
        self.dosexec("cls")
        self.print_program_title()

    def close(self):
        self.on = False
     

    def execute_comand(self):
        
        if self.command1 == 'close':
            self.close()

        if self.command1 == 'clear':
            self.clear()

        for cm in self.commands_list:
            # cprint(cm.COMMAND_NAME)
            if cm.COMMAND_NAME == self.commands :
                cm.exec(self.commands)


if __name__ == '__main__':
    CrawlerUCLI().parse_args()
