# VLC Media Player RPC for Discord, for Windows
import sys
import signal
import requests
import getpass
import psutil
import time
import subprocess
from json import load, dump, JSONDecodeError
from os.path import isfile, join, exists
from os import getcwd
from sys import exit
from pypresence import Presence
from host import Host


host = Host()


def signal_handler(signal, frame):
    # print("Exiting vlc_rich")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)
# RPC = Presence(client_id)
# RPC.connect()


def vlc_running():
    '''
    Checks if vlc.exe is running
    '''
    for p in psutil.process_iter(attrs=['name']):
        try:
            if "vlc.exe" in (p.info['name']).lower():
                return True
        except:
            # print("Could not find a running instance of vlc")
            return False
    return False


def round_tot_mem(val=psutil.virtual_memory().total/1024/1024, unit="GB"):
    '''
    Returns a rounded number of the total memory of the computersystem in whole GigaBytes.\n
    Arguments:\n
    :param val: Total memory size in MegaBytes default is `psutil.virtual_memory().total/1024/1024` <type:int>\n
    :param unit: Unit for the return value [\'MB\' | \'GB\'], default is \'GB\' <type:str>
    '''
    for g in range(1, 4097):
        gg = g * 1024
        if val > gg - 512 and val < gg + 511:
            if unit.upper() == "MB":
                return gg
            elif unit.upper() == "GB":
                return gg/1024


class Vlc_Status():
    '''
    VLC Media Player Status Class\n
    Arguments:\n
    :param url: url for the vlc staus xml, typically: `http://localhost:8080/requests/status.xml` <type:str>\n
    :param username: Username for the VLC web interface, typically it's left blank <type:str>\n
    :param password: Password for the VLC web interface. You set this password when configuring the interface. <type:str>\n
    \n
    Methods:\n
    `get_music_info(self)`
    '''

    def __init__(self, url, username="", password=""):
        self.url = url
        self.username = username
        self.password = password
        retdata = requests.get(self.url, auth=(
            self.username, self.password))
        retdata.encoding = 'utf-8'
        self.data = retdata.text.replace(
            "&amp;#39;", "'").replace("&amp;amp;", "&")
        # print(self.data)

    def get_music_info(self):
        '''
        Returns title, artist and album of the currently played song in VLC Media Player.\n
        The data comes from the status.xml file that the web interface uses.\n
        Returns: <type:dict> with the keys: [\'title\', \'artist\', \'album\', \'status\']
        '''
        info_tag_e = '</info>'
        artist_tag_s = '<info name=\'artist\'>'
        artist_start = str(self.data).find(artist_tag_s)
        data = self.data[artist_start:]
        artist_start = 20
        artist_end = str(data).find(info_tag_e)
        artist = data[int(artist_start):int(artist_end)]
        # print(artist)
        data = str(self.data)
        album_tag_s = '<info name=\'album\'>'
        album_start = data.find(album_tag_s)
        data = data[album_start:]
        album_start = 19
        album_end = data.find(info_tag_e)
        album = data[album_start:album_end]
        # print(album)
        data = str(self.data)
        title_start_s = '<info name=\'title\'>'
        title_start = data.find(title_start_s)
        data = data[title_start:]
        title_start = 19
        title_end = data.find(info_tag_e)
        title = data[title_start:title_end]
        # print(title)
        data = str(self.data)
        state_start_s = '<state>'
        state_end_s = '</state>'
        state_start = data.find(state_start_s) + 7
        state_end = data.find(state_end_s)
        state = data[state_start:state_end]
        state = state[0].upper() + state[1:].lower()
        # print(data)
        return {'artist': artist, 'album': album, 'title': title, 'state': state}


def get_json_value_from_key(key):
    '''
    Decodes the 'client.json' file and retrieves the client id for the discord app.\n
    If you don't have an client id for your user then please read the article: \n
    https://discord.com/developers/docs/game-sdk/sdk-starter-guide \n
    Otherwise if you have a client id setup for your custom app then just paste it in the json file.\n
    get_json_value_from_key() -> str
    '''
    if not exists(join(getcwd(), 'client.json')):
        print(f"The JSON file could not be found or does not exist!\nCreating new JSON file...")
        f = open("client.json", "w")
        data = {
            "client_id": "",
            "pwd": ""
        }
        dump(data, f, indent=2)
        f.close()
        exit(1)
    try:
        f = open("client.json", "r")
        try:
            if not isfile(join(getcwd(), 'client.json')):
                print(f"Path {join(getcwd(), client_id)} is not a file, but a directory!")
                return ""
            client_id = load(f)[str(key)]
            f.close()
            return client_id
        except JSONDecodeError as e:
            f.close()
            print(f"Unable to decode JSON file!\n{e}")
            exit(1)
        except KeyError as e:
            f.close()
            print(f"Key 'client_id' not found in the JSON file!\n{e}")
            exit(1)
    except FileNotFoundError as e:
        f.close()
        print(f"The JSON file could not be found or does not exist!\nCreating new JSON file...\n{e}")
        f = open("client.json", "w")
        data = {
            "client_id": "",
            "pwd": ""
        }
        dump(data, f, indent=2)
        f.close()
        exit(1)

currently_playing = ""

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1].lower() == ("/?" or "-?"):
        print("VLC Rich Presence for Discord. Switches: [/? | /s | /p]")
        print("\t/?\t                Display help.")
        print("\t/s\t                Run VLC Rich without any password specified.")
        print("\t/p \"password_for_vlc\"\tRun VLC Rich with a password specified as an argument")
        sys.exit(0)
    if len(sys.argv) == 2 and sys.argv[1].lower() == ("/s" or "-s"):
        password = ''
    elif len(sys.argv) == 3 and sys.argv[1].lower() == ("/p" or "-p"):
        password = str(sys.argv[2])
    else:
        password = get_json_value_from_key("pwd")
        while password == "":
            password = getpass.getpass('Password For VLC Web-interface: ')
    url = "http://localhost:8080/requests/status.xml"
    username = ''
    while True:
        while not vlc_running():
            # print("Could not find a running process of vlc")
            try:
                RPC.close()
            except:
                print("No connection to Discord has been made yet!")
            RPC = None
            client_id = ''
            time.sleep(2.5)
        try:
            client_id = get_json_value_from_key("client_id")
            if client_id == "":
                print(f"Client ID is missing!")
                exit(1)
            RPC = Presence(client_id, pipe=0)
            RPC.connect()
            '''ac = Activity(RPC)'''
        except:
            print("Unable to connect to Discord RPC.")
            sys.exit(0)
        while vlc_running():
            try:
                vlc_status = Vlc_Status(url, username, password)
                lis = vlc_status.get_music_info()
                '''print("You are listening to: %s by %s from %s" %
                      (lis["title"], lis["artist"], lis["album"]))
                print(lis["state"])'''
                if lis:
                    cmd = "WMIC CPU GET NAME"
                    cpu = subprocess.check_output(
                        cmd, shell=True).decode()
                    cpu = cpu.replace('\r', '').replace('\n', '').replace(
                        'Name                                      ', '').replace('  ', '').replace('(TM)', '').replace('(R)', '')
                    cpu = host.get_cpu(bare=True)
                    ram = "%d GB" % int(
                        (round_tot_mem(unit="GB")))
                    cmd = "WMIC PATH WIN32_VIDEOCONTROLLER GET NAME"
                    gpu_ = subprocess.check_output(cmd, shell=True).decode()
                    gpu = gpu_.split('\n')[1].replace('\r', '').replace('\n', '').replace('  ', '').replace(
                        'NVIDIA ', '').replace('AMD ', '').replace('INTEL ', '').replace('ATI ', '').replace('Intel(R)', '')
                    gpu = host.get_gpu(bare=True)
                    stats = "CPU: %s | \nRAM: %s | \nGPU: %s | \nCPU Usage: %d %% | \nRAM Usage: %d MB" % (
                        cpu, ram, gpu, int(psutil.cpu_percent()), psutil.virtual_memory().used/1024/1024)
                    #print(stats)
                    t = lis["title"]
                    a = lis["artist"]
                    b = lis["album"]
                    if currently_playing != f"{a} - {t}":
                        currently_playing = f"{a} - {t}"
                        print(currently_playing)
                    if (t and a and b) == "":
                        '''ac.state = lis["state"]
                        ac.details = "No Media Information Available."'''
                        RPC.update(large_image='vlc_inactive',
                                   large_text='No media information available.', small_image='vlc_i', small_text=stats)
                    else:
                        '''ac.state = lis["state"]
                        ac.details = lis["title"] + " by " + \
                            lis["artist"] + " from " + lis["album"]'''
                        img_text = lis['state'] + ": " + \
                            lis['title'] + " by " + lis['artist']
                        if lis['state'].lower() == 'playing':
                            RPC.update(state=lis["state"], details=lis["title"] + "\nby " + lis["artist"] + "\nfrom " +
                                       lis["album"], large_image='vlc_icon', large_text=img_text, small_image='icon', small_text=stats)
                        else:
                            RPC.update(state=lis["state"], details=lis["title"] + "\nby " + lis["artist"] + "\nfrom " + lis["album"],
                                       large_image='vlc_inactive', large_text=stats, small_image='vlc_i', small_text=img_text)
                time.sleep(2.5)
            except:
                pass
        #signal.signal(signal.SIGINT, signal_handler)
