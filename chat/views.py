import threading
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView
from django.db.models import Prefetch
from django.contrib import messages as django_messages
from chat.tools import CHAT_TOOLS, get_file_text
from documents.models import ContextFile
from documents.forms import FileUploadOrSelectForm
import os
from django.contrib.auth.models import User
from documents.signals import process_files
from services.forms import ParamsForm, SystemPromptForm
from services.models import LanguageModel, UserAPIKey, get_default_language_model
from .models import Chat, Message
from services.llm_handler import (
    call_api,
    get_markdown,
    handle_tools_calls,
    process_response,
    store_payload_and_usage,
)
from .forms import DeleteChatForm, MessageForm, UpdateChatForm


def update_chat(request, chat_id):
    if request.method == "POST":
        chat = Chat.objects.get(pk=chat_id)
        form = UpdateChatForm(request.POST, instance=chat)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Chat updated successfully")
        else:
            django_messages.error(request, "Error updating chat")
            return render(request, "chat/home.html", {"form": form})
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_chat(request, chat_id):
    if request.method == "POST":
        try:
            chat = Chat.objects.get(pk=chat_id)
            chat.delete()
        except Chat.DoesNotExist:
            django_messages.error(request, "Chat not found.")
    return redirect("chat")


def finalize_stream(
    message_to_populate: Message, text_generated: str, messages: list[dict]
):
    """Finalize and save the generated message content."""
    message_to_populate.sender = "assistant"
    message_to_populate.text = text_generated
    message_to_populate.markdown = get_markdown(text_generated)
    message_to_populate.save(update_fields=["sender", "text", "markdown"])
    chat = message_to_populate.chat
    messages.append({"role": "assisstang", "content": text_generated})
    if not chat.topic:
        chat.generate_chat_topic(messages)


def yield_chat_response_stream(
    message_to_populate: Message,
    messages: list[dict],
    language_model: LanguageModel,
    user: User,
    params: dict,
    tools: list[dict] = None,
    tool_functions: list[dict] = None,
):
    response = call_api(
        model=language_model,
        messages=messages,
        user=user,
        stream_flag=True,
        params=params,
        tools=tools,
    )

    chunk_responses = []
    # Process the response and yield as data comes in
    for chunk, generated_text_json, tool_calls, raw_text_generated in process_response(
        response
    ):
        chunk_responses.append(chunk.model_dump())
        yield f"data: {generated_text_json}\n\n"

    store_payload_and_usage(
        messages, chunk_responses, message_to_populate.request_config, user
    )

    if tool_calls:
        tools_response = handle_tools_calls(tool_calls, tool_functions)

        if tools_response:
            new_message = {"role": "system", "content": tools_response}
            messages.append(new_message)
            yield from yield_chat_response_stream(
                message_to_populate=message_to_populate,
                messages=messages,
                language_model=language_model,
                user=user,
                params=params,
                tools=None,
            )
    else:
        yield "event: close\n\n"
        finalize_stream(message_to_populate, raw_text_generated, messages)


def generate_stream(request, chat_id):
    chat = Chat.objects.get(pk=chat_id)
    msg_to_populate = Message.objects.get(chat=chat, sender="waiting")
    chat_history = chat.message_set.all().order_by("created_at")

    system_prompt = chat.request_config.system_prompt
    system_prompt = {"role": "system", "content": system_prompt}
    messages = [system_prompt]
    for msg in chat_history:
        if msg.sender != "waiting":
            messages.append({"role": msg.sender, "content": msg.text})
            if context_files := msg.context_files.all():
                for context_file in context_files:
                    messages.append(
                        {
                            "role": "system",
                            "content": f"The user has uploaded a file: **{os.path.basename(context_file.file.name)}** with context_file_id: {context_file.id}",
                        }
                    )

    return StreamingHttpResponse(
        yield_chat_response_stream(
            message_to_populate=msg_to_populate,
            messages=messages,
            language_model=chat.request_config.language_model,
            user=chat.user,
            params=chat.request_config.params,
            tools=CHAT_TOOLS,
            tool_functions={"get_file_text": get_file_text},
        ),
        content_type="text/event-stream; charset=utf-8",
    )


def send_message(request, chat_id=None):
    if request.method == "POST":
        curr_chat, created = Chat.objects.get_or_create(id=chat_id, user=request.user)
        form = MessageForm(request.POST)
        if form.is_valid():
            text = request.POST.get("text")
            language_model = form.cleaned_data["language_model"]
            request_config = curr_chat.request_config
            request_config.language_model = language_model
            request_config.save()
            if not UserAPIKey.objects.filter(
                user=request.user, api=language_model.api
            ).exists():
                django_messages.error(
                    request,
                    f"API key for {language_model.api.name} not found. Please add an API key in the Manage API Keys section.",
                )
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

            curr_chat.save()
            Message.objects.create(chat=curr_chat, text=text, sender="user")
            Message.objects.create(chat=curr_chat, text="", sender="waiting")
    if created:
        return redirect("chat", chat_id=curr_chat.id)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def process_uploaded_files(uploaded_files, chat: Chat):
    new_files = ContextFile.objects.bulk_create(
        [
            ContextFile(file=file, user=chat.user, filename=os.path.basename(file.name))
            for file in uploaded_files
        ]
    )
    thread = threading.Thread(
        target=process_files, args=(new_files, chat.request_config.language_model.name)
    )
    thread.start()
    file_names = ", ".join([os.path.basename(file.filename) for file in new_files])
    new_msg = chat.message_set.create(
        text=f"{len(new_files)} files uploaded: {file_names}",
        sender="user",
    )
    new_msg.context_files.add(*new_files)
    file_names_with_ids = ", ".join(
        [
            f"{os.path.basename(file.filename)} with context_file_id: {file.id}"
            for file in new_files
        ]
    )
    chat.message_set.create(
        text=f"These are the ids of the uploaded files: {file_names_with_ids}",
        sender="system",
    )


def process_selected_files(selected_files, chat):
    file_names = ", ".join([os.path.basename(file.filename) for file in selected_files])
    new_msg = chat.message_set.create(
        text=f"{len(selected_files)} files selected: {file_names}",
        sender="user",
    )
    new_msg.context_files.add(*selected_files)
    file_names_with_ids = ", ".join(
        [
            f"{os.path.basename(file.filename)} with context_file_id: {file.id}"
            for file in selected_files
        ]
    )
    chat.message_set.create(
        text=f"These are the ids of the selected files: {file_names_with_ids}",
        sender="system",
    )


def add_file_to_chat(request, chat_id=None):
    chat = Chat.objects.get(id=chat_id) if chat_id else None
    referer_is_new_chat = request.META.get("HTTP_REFERER", "").endswith("chat/new")
    no_chats = Chat.objects.count() == 0
    if not chat and (referer_is_new_chat or no_chats):
        chat = Chat.objects.create(user=request.user)

    if request.method == "POST":
        form = FileUploadOrSelectForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_files = form.cleaned_data.get("uploaded_files")
            selected_files = form.cleaned_data.get("selected_files")
            if uploaded_files:
                process_uploaded_files(uploaded_files, chat)
            if selected_files:
                process_selected_files(selected_files, chat)

            if not uploaded_files and not selected_files:
                django_messages.error(request, "You must select or upload files.")
        else:
            django_messages.error(request, form.errors)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class ChatListView(ListView):
    model = Chat  # Model that the ListView will handle
    template_name = "chat/chat.html"  # Template for rendering the view
    context_object_name = "chats"  # The name of the context variable in the template

    def dispatch(self, request, *args, **kwargs):
        chat_id = self.kwargs.get("chat_id")
        if not chat_id:
            first_chat = Chat.objects.filter(user=self.request.user).first()
            if first_chat:
                return redirect("chat", chat_id=first_chat.id)
        elif chat_id == "new":
            self.kwargs.pop("chat_id")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Override get_queryset to filter the chats and prefetch the latest message
        if self.request.user.is_anonymous:
            return Chat.objects.none()
        queryset = (
            Chat.objects.filter(user=self.request.user)
            .prefetch_related(
                Prefetch(
                    "message_set",
                    queryset=Message.objects.order_by("-created_at"),
                    to_attr="messages",  # Custom attribute for the prefetched messages
                )
            )
            .order_by("-created_at")
        )

        return queryset

    def get_context_data(self, **kwargs):
        if self.request.user.is_anonymous:
            return super(ChatListView, self).get_context_data(**kwargs)

        context = super(ChatListView, self).get_context_data(**kwargs)
        chat_id = None
        chat_id = self.kwargs.get("chat_id")

        if chat_id:
            context["current_chat"] = Chat.objects.get(id=chat_id)
            context["chat_messages"] = Message.objects.filter(
                chat_id=chat_id, sender__in=["user", "assistant", "waiting"]
            ).order_by("created_at")
            context["context_files"] = ContextFile.objects.filter(
                message__chat__id=chat_id
            ).distinct()
            if context["chat_messages"]:
                last_message = context["chat_messages"].latest("created_at")
                if last_message.sender == "waiting":
                    context["generate_response"] = True

            language_model = (
                context["current_chat"].get_last_message().request_config.language_model
            )
        else:
            language_model = get_default_language_model()

        context["chat_forms"] = [
            {
                "chat_id": chat.id,
                "request_config_id": chat.request_config.id,
                "system_prompt_form": SystemPromptForm(instance=chat.request_config),
                "params_form": ParamsForm(instance=chat.request_config),
                "update_chat_form": UpdateChatForm(instance=chat),
                "delete_chat_form": DeleteChatForm(instance=chat),
            }
            for chat in context["chats"]
        ]

        context["message_form"] = MessageForm(
            initial={"language_model": language_model}
        )
        context["file_upload_form"] = FileUploadOrSelectForm()
        return context
