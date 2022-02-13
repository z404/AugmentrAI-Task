from textwrap import indent
import requests
import json

rasa_url = "http://localhost:8080"

#testing message endpoint
endpoint = "/webhooks/rest/webhook"
args = {"sender":"anish","message":"yes, thank you"}
print(requests.post(rasa_url+endpoint, json=args).content)

#getting conversation
endpoint = "/conversations/anish/tracker"
print(indent(json.dumps(requests.get(rasa_url+endpoint).json(), indent=4), ' '*4))

# endpoint = "/webhooks/rest"
# print(requests.get(rasa_url+endpoint).content)