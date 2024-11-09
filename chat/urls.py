from django.urls import path
from . import views

urlpatterns = [
    path("", views.ChatListView.as_view(), name="chat"),
    path("<str:chat_id>", views.ChatListView.as_view(), name="chat"),
    path("update_chat/<str:chat_id>", views.update_chat, name="update_chat"),
    path("delete_chat/<str:chat_id>", views.delete_chat, name="delete_chat"),
    # path("update_params/<str:chat_id>", views.update_params, name="update_params"),
    # path(
    #     "update_system_prompt/<str:chat_id>",
    #     views.update_system_prompt,
    #     name="update_system_prompt",
    # ),
    path("add_file/", views.add_file_to_chat, name="add_file_to_chat"),
    path("add_file/<str:chat_id>/", views.add_file_to_chat, name="add_file_to_chat"),
    path("send_message/<str:chat_id>", views.send_message, name="send_message"),
    path("send_message/", views.send_message, name="send_message"),
    path(
        "generate_stream/<str:chat_id>", views.generate_stream, name="generate_stream"
    ),
]
