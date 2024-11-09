from django.contrib import admin
from .models import (
    RequestConfiguration,
    UserAPIKey,
    ModelAPI,
    LanguageModel,
    TokenUsage,
)


class ModelAPIAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)


admin.site.register(ModelAPI, ModelAPIAdmin)


class LanguageModelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)


admin.site.register(LanguageModel, LanguageModelAdmin)


class UsageAdmin(admin.ModelAdmin):
    list_display = (
        "payload_sent",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    )
    search_fields = ("payload_sent",)
    list_filter = ("payload_sent",)


admin.site.register(TokenUsage, UsageAdmin)


class APIKEYAdmin(admin.ModelAdmin):
    list_display = (
        "api",
        "user",
        "key",  # you are able to see this but it only with the right encryption key
        "encrypted_key",
        "created_at",
    )
    search_fields = ("api",)
    list_filter = ("api",)


admin.site.register(UserAPIKey, APIKEYAdmin)


class RequestConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "params",
        "system_prompt",
        "language_model",
    )
    search_fields = ("params",)
    list_filter = ("params",)


admin.site.register(RequestConfiguration, RequestConfigurationAdmin)
