from textwrap import indent
import requests
import json
from colorama import Fore, Back, Style, init
import os

init(autoreset=True)

#testing message endpoint
endpoint = "/webhooks/rest/webhook"
os.system('cls' if os.name == 'nt' else 'clear')

print(Fore.GREEN + "Rasa Interaction Program\n")
rasa_url = input(Fore.CYAN + "Please enter the URL of your Rasa instance (default = http://localhost:8000): ")
if rasa_url == "":
    rasa_url = "http://localhost:8000"
user = input(Fore.CYAN + "Please enter your name (default = \"test\"): ")
if user == "":
    user = "test"

os.system('cls' if os.name == 'nt' else 'clear')

while True:
    message = input(Fore.LIGHTMAGENTA_EX + " >> ")
    if message == "exit":
        break
    elif message == "tracker":
        endpointtracker = "/conversations/"+user+"/tracker"
        response = requests.get(rasa_url + endpointtracker)
        print(Fore.WHITE + "Writing to file...")
        with open("tempfile.txt", "w") as f:
            f.write(json.dumps(response.json(), indent=4))
        continue
    elif message == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        continue
    payload = {
        "sender": user,
        "message": message
    }
    response = requests.post(rasa_url + endpoint, json=payload)
    try:
        for i in response.json():
            if i['text'] != "":
                print(Fore.WHITE + i['text'])
            else:
                print(Fore.RED + "The bot did not reply")
    except Exception as e:
        print(Fore.RED + "Oh no, something went wrong! Error: " + str(e))
        print("response: " + str(response.json()))