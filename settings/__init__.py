import os
import tkinter as tk
from json import dump, load, JSONDecodeError
from tkinter.filedialog import asksaveasfile, askopenfilename
from sys import exit
from getpass import getpass
from pathlib import Path

__author__ = "Truls Skadberg (Scadic)"
__copyright__ = "Copyright 2021, Scadic"
__credits__ = "Truls Skadberg (Scadic)"

__version__ = "1.0.0"
__maintainer__ = "Truls Skadberg (Scadic)"
__email__ = "trulshskadberg@gmail.com"
__status__ = "Production"

def get_input(promt="", t=str):
    '''
    Gets input from `input` and evaluates if the data is of the correct type.
    If not it will ask again until it is of the correct type.\n
    Parameters:\n
    :prompt (str): The string which is sent to `input`'s prompt.
    :t (class): The class of the return value. Only single classes i.e. <type:str>, <type:int>...\n
    get_input(`prompt`, `t`) -> t(`get_input(prompt)`)
    '''
    if t == None or type(t) is None:
        print("Cannot use None as the type as it is not callable, use a suitable type for your data!")
        return None
    while True and t != None:
        i = input(promt)
        try:
            i = t(i)
        except ValueError as e:
            print("Unable to parse the value to the type %s, please try again." % str(t))
        except TypeError as e:
            print("Unable to call %s because %s" % (t, e))
        if type(i) is t:
            break
    return i

def prompts():
    '''
    Uses `get_input` and `getpass` to request data from the user to setup parameters for ServerSettings.\n
    prompts() -> dict{str: str}
    '''
    return {
        "client_id": get_input("Enter the client_id for the app: ", str),
        "permissions": get_input("Enter the permissions integer for the app: ", int),
        "token": get_input("Enter the token for the app: ", str)
    }

def __get_path__(path=None):
    '''
    Gets the path for the settings file from settings_path.json.
    If no path is found it will return an empty string.\n
    Parameters:\n
    :path (str): The path of settings_path.json.\n
    __get_path__(path) -> str
    '''
    path = path or os.path.join(os.getcwd(), 'settings_path.json')
    if not os.path.isfile(path):
        print("Path: '%s' is not a file, but a directory!" % path)
        return ""
    try:
        f = open(path, 'r')
        try:
            p = load(f)["path"]
            if not os.path.isfile(p):
                print("Path: '%s' is not a file, but a directory!" % p)
                return ""
            return p
        except JSONDecodeError as e:
            print("Unable to decode JSON file!\n%s" % str(e))
            exit(1)
        except KeyError as e:
            print("Key 'path' not found in the JSON file!\n%s" % str(e))
            return ""
    except FileNotFoundError as e:
        print("The JSON file could not be found or does not exist!\n%s" % str(e))
        return ""
    finally:
        f.close()
    return ""

def __save_path__(path=None, data=""):
    '''
    Saves the path of the settings file to 'settings_path.json'\n
    :path (str): Path to 'settings_path.json' file.\n
    :data (str)" Path to the settings file.\n
    __save_path__(path, data) -> None
    '''
    d = {'path': str(data)}
    path = path or os.path.join(os.getcwd(), 'settings_path.json')
    try:
        f = open(path, 'w')
        dump(d, f, indent=2)
    except FileNotFoundError as e:
        print("Unable to find the file: %s\n%s" % (path, e))
        exit(1)
    finally:
        f.close()

class ServerSettings():
    '''
    ServerSettings which holds a dict loaded from a JSON file or user input.
    It also has the keys as attributes for their corressponding values.
    '''
    def __init__(self, json_settings_file=__get_path__(), new=False):
        '''
        Tries to use the supplied path to a json settings file to load settings for the server.
        If it encounters errors or no files, you may be prompted for input or the program may exit.\n
        Parameters:\n
        :json_settings_file (str): Full path to the settings json file.\n
        :new (bool): True or False depending if you want to create new settings or not.
        __init__(`self`, `json_settings_file`, `new`) -> ServerSettings
        '''
        root = tk.Tk()
        root.withdraw()
        if json_settings_file == "" or not os.path.exists(json_settings_file) or new:
            if new:
                print("Creating new ServerSettings...")
                self.settings = prompts()
                self.__setattrs__()
                p = self.__save_settings__()
                __save_path__(p)
            elif not os.path.exists(json_settings_file):
                print("Cannot find the server settings file!\n \
                \rFile may have been deleted or you do not have access to the file.\
                    \rPlease either stop the server or input the required data to start the application.")
                self.__load_settings__()
            if not hasattr(self, "settings"):
                print("No settings!\nPlease remember where your server settings file is located!")
                self.settings = prompts()
                self.__setattrs__()
                p = self.__save_settings__()
                __save_path__(p)
        elif os.path.exists(json_settings_file):
            with open(json_settings_file) as f:
                try:
                    self.settings = load(f)
                    self.__setattrs__()
                except JSONDecodeError as e:
                    print("Error Unable to decode JSON data!\n%s" + str(e))
                    exit(1)
                self.print_settings()

    def print_settings(self):
        '''
        Prints the settings in an ServerSettings instance. 
        Password will only be printed with '*' representing any type of character.
        '''
        print("Loading Server Settings...")
        print("{")
        for k, v in self.settings.items():
            if k == "password" or k in ["pwd", "client_id", "token"]:
                print("\t%s:\t" % k + "*"*len(v))
            else:
                print("\t%s:\t%s" % (k, v))
        print("}")

    def __setattrs__(self):
        '''
        Loop through `self.settings` and set them as attributes.
        If there is no `settings` attribute it will return {}.\n
        __setattrs__(`self`) -> dict{'str': 'str'}
        '''
        if hasattr(self, "settings"):
            for k, v in self.settings.items():
                self.__setattr__(k, v)
            return self.settings
        else:
            return {}

    def __save_settings__(self):
        '''
        Method for saving the contents of `self.settings` to a json file.
        And returns the filename of where the json file is located.\n
        __save_settings__(`self`) -> str
        '''
        f = asksaveasfile(mode="w", filetypes=[('JSON', '*.json')], defaultextension=('JSON', '*.json'))
        if not f:
            print("File save cancelled!")
            return ""
        dump(self.settings, f, indent=2)
        return str(f.name)

    def __load_settings__(self):
        '''
        Method for loading a json file.
        Returns the loaded settings in a dict.\n
        __load_settings__(`self`) -> dict{'str': 'str'}
        '''
        f = askopenfilename()
        if not f:
            print("No File Loaded!\nRequesting User Input!")
            self.settings = prompts()
            a = self.__setattrs__()
            r = self.__save_settings__()
            __save_path__(data=r)
            return r
        else:
            with open(f, 'r') as reader:
                try:
                    self.settings = load(reader)
                    self.__setattrs__()
                    __save_path__(data=reader.name)
                except JSONDecodeError as e:
                    print("Unable to decode JSON data!")
                    self.settings = prompts()
                    self.__setattrs__()
                    r = self.__save_settings__()
                    __save_path__(data=r)
                self.print_settings()
                reader.close()
            return self.settings