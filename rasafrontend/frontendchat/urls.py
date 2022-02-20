from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('chat/post/', views.chat_api_req, name='chat_api_req'),
]