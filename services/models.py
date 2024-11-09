from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from config.settings import ENCRYPTION_KEY
from django.db.models import Q


def _get_default_params():
    return {"temperature": 1.0, "top_p": 1.0}.copy()


def get_default_system_prompt():
    return """You are a helpful assistant!"""


def get_default_language_model():
    language_model, created = LanguageModel.objects.get_or_create(name="gpt-4o-mini")
    return language_model


class ModelAPI(models.Model):
    identifier = models.CharField(max_length=100, default="openai", unique=True)
    name = models.CharField(max_length=100, default="OpenAI")
    base_url = models.CharField(max_length=100, default="https://api.openai.com/v1/")

    def __str__(self):
        return self.identifier


class LanguageModel(models.Model):
    name = models.CharField(max_length=100, default="gpt-4o-mini", unique=True)
    context_window = models.PositiveIntegerField(default=128000)
    api = models.ForeignKey(ModelAPI, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name


class RequestConfiguration(models.Model):
    params = models.JSONField(default=_get_default_params)
    system_prompt = models.TextField(default=get_default_system_prompt)
    language_model = models.ForeignKey(
        LanguageModel, on_delete=models.CASCADE, default=get_default_language_model
    )

    def __str__(self):
        return self.language_model.name


def get_default_request_config():
    # Define default values for comparison
    default_params = _get_default_params()
    default_system_prompt = get_default_system_prompt()
    default_language_model = get_default_language_model()

    # Check for an existing config that matches these defaults
    existing_config = RequestConfiguration.objects.filter(
        Q(params=default_params)
        & Q(system_prompt=default_system_prompt)
        & Q(language_model=default_language_model)
    ).first()

    # Return the existing default config, or create a new one if none exists
    if existing_config:
        return existing_config
    else:
        return RequestConfiguration.objects.create(
            params=default_params,
            system_prompt=default_system_prompt,
            language_model=default_language_model,
        )


class PayloadSent(models.Model):
    request_config = models.ForeignKey(RequestConfiguration, on_delete=models.CASCADE)
    payload = models.JSONField()
    response = models.JSONField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payload)


class TokenUsage(models.Model):
    payload_sent = models.ForeignKey(PayloadSent, on_delete=models.CASCADE)
    prompt_tokens = models.PositiveIntegerField(null=True)
    completion_tokens = models.PositiveIntegerField(null=True)
    total_tokens = models.PositiveIntegerField(null=True)
    prompt_tokens_details = models.JSONField(null=True)
    completion_tokens_details = models.JSONField(null=True)

    def __str__(self):
        return f"{self.total_tokens} tokens used"


class UserAPIKey(models.Model):
    api = models.ForeignKey(ModelAPI, on_delete=models.CASCADE)
    encrypted_key = models.BinaryField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.api.identifier + " key"

    @property
    def key(self):
        cipher_suite = Fernet(ENCRYPTION_KEY)
        return (
            cipher_suite.decrypt(self.encrypted_key).decode()
            if self.encrypted_key
            else None
        )

    @key.setter
    def key(self, value):
        cipher_suite = Fernet(ENCRYPTION_KEY)
        self.encrypted_key = cipher_suite.encrypt(value.encode())
