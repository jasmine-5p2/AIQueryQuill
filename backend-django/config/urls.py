from django.contrib import admin
from django.urls import path
from chat.views import health, register, login, chats, chat_messages, delete_chat, chat_stream
urlpatterns = [path("admin/", admin.site.urls), path("api/health/", health), path("api/auth/register/", register), path("api/auth/login/", login), path("api/chats/", chats), path("api/chats/<int:chat_id>/messages/", chat_messages), path("api/chats/<int:chat_id>/", delete_chat), path("api/chat/", chat_stream)]
