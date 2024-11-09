import threading
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from chat.models import Chat, Message
from documents.forms import FileUploadForm
from documents.models import ContextFile
import os
from django_tables2 import SingleTableView
from documents.tables import ContextFileTable
from documents.forms import FileDeleteForm
from .signals import process_files


def upload_file(request, chat_id=None):
    if request.method == "POST":
        # Retrieve chat if chat_id is provided, otherwise create a new chat based on referrer
        chat, created = (
            Chat.objects.get_or_create(pk=chat_id) if chat_id else (None, False)
        )
        referer_is_new_chat = request.META.get("HTTP_REFERER", "").endswith("chat/new")
        no_chats = Chat.objects.count() == 0
        if created and (referer_is_new_chat or no_chats):
            chat = Chat.objects.create(user=request.user)

        # Process the form and handle file uploads
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist("files")
            language_model = form.cleaned_data.get("language_model")

            file_names = [os.path.basename(file.name) for file in files]
            new_context_files = []
            for file in files:
                kwargs = {
                    "file": file,
                    "user": request.user,
                    "filename": os.path.basename(file.name),
                }
                new_context_files.append(ContextFile(**kwargs))
            ContextFile.objects.bulk_create(new_context_files)

            # If chat exists, create a message and link files to it
            if chat:
                message = Message.objects.create(
                    chat=chat,
                    text=f"{len(files)} file(s) uploaded: {', '.join(file_names)}",
                    sender="user",
                )

            thread = threading.Thread(
                target=process_files, args=(new_context_files, language_model.name)
            )
            thread.start()

    # Redirect to the previous page
    if chat:
        return redirect("chat", chat_id=chat.id)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_file(request, file_id):
    if request.method == "POST":
        file = ContextFile.objects.get(pk=file_id)
        file.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class ContextFileListView(SingleTableView):
    model = ContextFile
    table_class = ContextFileTable
    template_name = "documents/context_files.html"
    context_object_name = "context_files"
    table_pagination = {"per_page": 10}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FileUploadForm()
        if context["context_files"]:
            context["file_forms"] = [
                {"delete_form": FileDeleteForm(instance=context_file)}
                for context_file in context["context_files"]
            ]
        return context


def context_file_details(request, file_id):
    context_file = ContextFile.objects.get(pk=file_id)
    return render(
        request, "documents/context_file_details.html", {"context_file": context_file}
    )
