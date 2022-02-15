from textwrap import indent
import requests
import json

rasa_url = "http://localhost:5005"

#testing message endpoint
endpoint = "/webhooks/rest/webhook"

while True:
    print("\n\n")
    print("Enter your message:")
    message = input()
    if message == "exit":
        break
    elif message == "intent":
        endpointtracker = "/conversations/randomdude103/tracker"
        response = requests.get(rasa_url + endpointtracker)
        with open("tempfile.txt", "w") as f:
            f.write(json.dumps(response.json(), indent=4))
        continue

    payload = {
        "sender": "randomdude103",
        "message": message
    }
    response = requests.post(rasa_url + endpoint, json=payload)
    for i in response.json():
        if i['text'] != "":
            print(i['text'])
        else:
            print("The bot did not reply")

#getting conversation
# endpoint = "/conversations/anish/tracker"
# print(indent(json.dumps(requests.get(rasa_url+endpoint).json(), indent=4), ' '*4))

# endpoint = "/webhooks/rest"
# print(requests.get(rasa_url+endpoint).content)