import uuid
from django.db import models
from django.contrib.auth.models import User
from documents.models import ContextFile
from services.llm_handler import call_api
from services.models import (
    RequestConfiguration,
    PayloadSent,
    TokenUsage,
    get_default_request_config,
)


class BaseContentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # Default ordering for all child models

    def __str__(self):
        return self.topic


class Chat(BaseContentModel):
    request_config = models.ForeignKey(
        RequestConfiguration,
        on_delete=models.CASCADE,
        default=get_default_request_config,
    )

    def __str__(self):
        return self.topic

    def generate_chat_topic(self, messages):
        text = f"Based on this message, what name would you give to this chat? {messages} Just provide the title without quotes or anything, nothing else."
        payload = [{"role": "user", "content": text}]
        response = call_api(
            model=self.request_config.language_model, messages=payload, user=self.user
        )
        request_config_copy = self.request_config
        request_config_copy.pk = None
        request_config_copy.save()
        payload_sent = PayloadSent.objects.create(
            request_config=request_config_copy,
            payload=payload,
            user=self.user,
            response=response.model_dump(),
        )

        TokenUsage.objects.create(
            payload_sent=payload_sent, **response.usage.model_dump()
        )

        self.topic = response.choices[0].message.content
        self.save()

    def get_last_message(self):
        return self.message_set.latest("created_at")

    def get_assistant_messages_count(self):
        return self.message_set.filter(sender="assistant").count()

    def get_chat_token_count(self):
        last_message = self.get_last_message()
        payload_sent = PayloadSent.objects.filter(
            request_config=last_message.request_config
        )
        payload_sent = payload_sent.latest("created_at")
        token_usage = TokenUsage.objects.get(payload_sent=payload_sent)

        return token_usage.total_tokens

    def get_context_window_percentage(self):
        token_count = self.get_chat_token_count()
        percentage = (
            token_count / self.request_config.language_model.context_window
        ) * 100
        return f"{percentage:.2f} %"

    def get_context_window_percentage_float(self):
        token_count = self.get_chat_token_count()
        percentage = (
            token_count / self.request_config.language_model.context_window
        ) * 100
        return percentage

    def get_last_message_sender(self):
        return self.get_last_message().sender


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    request_config = models.ForeignKey(
        RequestConfiguration, on_delete=models.CASCADE
    )  # this one copies the current chat's request config
    context_files = models.ManyToManyField(ContextFile, blank=True)
    text = models.TextField()
    markdown = models.TextField(blank=True, null=True)
    sender = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        try:
            request_config = self.request_config
        except:
            request_config = self.chat.request_config
            request_config.pk = None
            request_config.save()
            self.request_config = request_config
        super().save(*args, **kwargs)
