from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
import requests
import json

def index(request):
    return render(request, 'index.html')

def _get_chat_history(rasaurl, username):
    endpointtracker = "/conversations/"+username+"/tracker"
    try:
        response = requests.get(rasaurl + endpointtracker).json()["events"]
        response.sort(key=lambda x: x['timestamp'])
        lst = [(i['event'],i['text']) for i in response if i["event"] == "user" or i["event"] == "bot"]
    except:
        lst = []

    return lst

def chat(request):
    if request.method == 'POST':
        message = dict(request.POST)
        if message['rasaurl'][0] == "":
            message['rasaurl'][0] = " http://4ad2-49-207-210-139.ngrok.io"
        if message['uname'][0] == "":
            message['uname'][0] = "test"
        message['rasaurl'][0] = message['rasaurl'][0].rstrip('/')
        try:
            message_history = _get_chat_history(message['rasaurl'][0], message['uname'][0])
            response = render(request, 'chat.html', {'chat_history': message_history, "uname": message['uname'][0]})
            response.set_cookie('rasaurl', message['rasaurl'][0])
            response.set_cookie('uname', message['uname'][0])
        except requests.exceptions.ConnectionError:
            return HttpResponse("Rasa server not found. Please check url and try again.")
        return response
    else:
        uname = request.COOKIES.get('uname')
        rasaurl = request.COOKIES.get('rasaurl')
        if rasaurl == None:
            return HttpResponse("Rasa url not found. Please go to the home page and try again.")
        try:
            message_history = _get_chat_history(rasaurl, uname)
            response = render(request, 'chat.html', {'chat_history': message_history, "uname": uname})
            response.set_cookie('rasaurl', rasaurl)
            response.set_cookie('uname', uname)
            return response
        except requests.exceptions.ConnectionError:
            return HttpResponse("Rasa server not found. Please check url and try again.")
        pass

def chat_api_req(request):
    if request.method == 'POST':
        rasaurl = request.COOKIES.get('rasaurl')
        post_data = json.loads(request.body.decode("utf-8"))
        reply = _send_message_to_bot(rasaurl, post_data['uname'], post_data['input'])
        return HttpResponse(json.dumps(reply), content_type="application/json")

def _send_message_to_bot(rasaurl, uname, message):
    endpoint = "/webhooks/rest/webhook"
    payload = {
        "sender": uname,
        "message": message
    }
    response = requests.post(rasaurl + endpoint, json=payload)
    
    reply = []

    try:
        if response.json() != []:
            for i in response.json():
                if i['text'] != "":
                    reply.append(i['text'])
        else:
            reply.append("The bot did not reply")
    except Exception as e:
        reply.append("Oh no, something went wrong! Error: " + str(e))
    
    return reply