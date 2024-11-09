from django.urls import path
from . import views

urlpatterns = [
    path("context_files/", views.ContextFileListView.as_view(), name="context_files"),
    path(
        "context_file_details/<int:file_id>",
        views.context_file_details,
        name="context_file_details",
    ),
    path("upload_file/", views.upload_file, name="upload_file"),
    path("upload_file/<str:chat_id>", views.upload_file, name="upload_file"),
    path("delete_file/<int:file_id>", views.delete_file, name="delete_file"),
]
