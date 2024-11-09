from django.db.models.signals import post_migrate
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserAPIKey, ModelAPI, LanguageModel
from dotenv import load_dotenv
import os


@receiver(post_migrate)
def create_default_language_model(sender, **kwargs):
    if not LanguageModel.objects.exists():
        openai_api, created = ModelAPI.objects.get_or_create(name="OpenAI")
        LanguageModel.objects.get_or_create(name="gpt-4o-mini", api=openai_api)
        mistral_api, created = ModelAPI.objects.get_or_create(
            name="Mistral", base_url="https://api.mistral.ai/v1/", identifier="mistral"
        )
        LanguageModel.objects.get_or_create(name="pixtral-12b", api=mistral_api)


@receiver(user_logged_in)
def load_api_keys_on_first_login(sender, request, user, **kwargs):
    load_dotenv()
    if (
        OPENAI_API_KEY := os.getenv("OPENAI_API_KEY")
    ) and not UserAPIKey.objects.filter(user=user, api__identifier="openai").exists():
        openai_api = ModelAPI.objects.get(identifier="openai")
        UserAPIKey.objects.create(api=openai_api, key=OPENAI_API_KEY, user=user)

    if (
        MISTRAL_API_KEY := os.getenv("MISTRAL_API_KEY")
    ) and not UserAPIKey.objects.filter(user=user, api__identifier="mistral").exists():
        mistral_api = ModelAPI.objects.get(identifier="mistral")
        UserAPIKey.objects.create(api=mistral_api, key=MISTRAL_API_KEY, user=user)
