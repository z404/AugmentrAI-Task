from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
import requests

def index(request):
    return render(request, 'index.html')

def get_chat_history(rasaurl, username):
    endpointtracker = "/conversations/"+username+"/tracker"
    response = requests.get(rasaurl + endpointtracker).json()["events"]
    response.sort(key=lambda x: x['timestamp'])
    lst = [(i['event'],i['text']) for i in response if i["event"] == "user" or i["event"] == "bot"]

    return lst

def chat(request):
    if request.method == 'POST':
        message = dict(request.POST)
        if message['rasaurl'][0] == "":
            message['rasaurl'][0] = "http://f75e-49-207-210-139.ngrok.io"
        if message['uname'][0] == "":
            message['uname'][0] = "test"
        message['rasaurl'][0] = message['rasaurl'][0].rstrip('/')
        message_history = get_chat_history(message['rasaurl'][0], message['uname'][0])
        response = render(request, 'chat.html', {'chat_history': message_history})
        response.set_cookie('rasaurl', message['rasaurl'][0])
        response.set_cookie('uname', message['uname'][0])
        return response
    else:
        # get request, make get from cookies
        # if cookies doesnt work, send to index
        pass