from django.shortcuts import render
from django.views.generic import ListView
from django.http import HttpResponseRedirect
from .forms import (
    DeleteAPIKeyForm,
    ParamsForm,
    RegisterLanguageModelForm,
    SystemPromptForm,
    UpdateModelAPIForm,
    CreateAPIKeyForm,
    RegisterModelAPIForm,
    DeleteModelAPIForm,
    UpdateLanguageModelForm,
    DeleteLanguageModelForm,
)
from .models import (
    RequestConfiguration,
    UserAPIKey,
    LanguageModel,
    ModelAPI,
    TokenUsage,
)
from django.contrib import messages as django_messages
from django_tables2 import SingleTableView
from .tables import ModelAPITable, UsageTable


def api_keys(request):
    form = CreateAPIKeyForm()
    api_keys = UserAPIKey.objects.filter(user=request.user)
    api_key_forms = [
        {
            "id": api_key.id,
            "delete_form": DeleteAPIKeyForm(instance=api_key),
        }
        for api_key in api_keys
    ]
    return render(
        request,
        "apis/api_keys.html",
        {"form": form, "api_keys": api_keys, "api_key_forms": api_key_forms},
    )


def create_api_key(request):
    if request.method == "POST":
        form = CreateAPIKeyForm(request.POST)
        if form.is_valid():
            user = request.user
            api_key = form.save(commit=False)
            api_key.user = user
            api_key.save()
        else:
            django_messages.error(request, form.errors)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_api_key(request, key_id):
    api_key = UserAPIKey.objects.get(pk=key_id)
    if request.method == "POST":
        form = DeleteAPIKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            api_key.delete()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def create_api(request):
    if request.method == "POST":
        form = RegisterModelAPIForm(request.POST)
        if form.is_valid():

            form.save()
        else:
            django_messages.error(request, form.errors)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def update_api(request, api_id):
    api = ModelAPI.objects.get(pk=api_id)
    if request.method == "POST":
        form = UpdateModelAPIForm(request.POST, instance=api)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_api(request, api_id):
    api = ModelAPI.objects.get(pk=api_id)
    if request.method == "POST":
        form = DeleteModelAPIForm(request.POST, instance=api)
        if form.is_valid():
            api.delete()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def create_language_model(request):
    if request.method == "POST":
        form = RegisterLanguageModelForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            django_messages.error(request, form.errors)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def update_language_model(request, language_model_id):
    language_model = LanguageModel.objects.get(pk=language_model_id)
    if request.method == "POST":
        form = UpdateLanguageModelForm(request.POST, instance=language_model)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_language_model(request, language_model_id):
    language_model = LanguageModel.objects.get(pk=language_model_id)
    if request.method == "POST":
        form = DeleteLanguageModelForm(request.POST, instance=language_model)
        if form.is_valid():
            language_model.delete()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def update_params(request, request_config_id):
    request_config = RequestConfiguration.objects.get(pk=request_config_id)
    if request.method == "POST":
        form = ParamsForm(request.POST, instance=request_config)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Parameters updated successfully.")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def update_system_prompt(request, request_config_id):
    request_config = RequestConfiguration.objects.get(pk=request_config_id)
    if request.method == "POST":
        form = SystemPromptForm(request.POST, instance=request_config)
        if form.is_valid():
            form.save()
            django_messages.success(request, "System prompt updated successfully.")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class LanguageModelListView(ListView):
    model = LanguageModel
    template_name = "apis/language_models.html"
    context_object_name = "language_models"

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return LanguageModel.objects.none()

        queryset = LanguageModel.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["register_language_model_form"] = RegisterLanguageModelForm()
        if "language_models" in context:
            context["language_model_forms"] = [
                {
                    "id": language_model.id,
                    "edit_form": UpdateLanguageModelForm(instance=language_model),
                    "delete_form": DeleteLanguageModelForm(instance=language_model),
                }
                for language_model in context["language_models"]
            ]
        return context


class UsageListView(SingleTableView):
    model = TokenUsage
    table_class = UsageTable
    template_name = "apis/usage.html"
    context_object_name = "usages"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        queryset = TokenUsage.objects.filter(
            payload_sent__user=self.request.user
        ).order_by("-payload_sent__created_at")
        return queryset


class ModelAPIListView(SingleTableView):
    model = ModelAPI
    table_class = ModelAPITable
    template_name = "apis/apis.html"
    context_object_name = "apis"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        queryset = ModelAPI.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["register_api_form"] = RegisterModelAPIForm()
        if "apis" in context:
            context["api_forms"] = [
                {
                    "id": api.id,
                    "edit_form": UpdateModelAPIForm(instance=api),
                    "delete_form": DeleteModelAPIForm(instance=api),
                }
                for api in context["apis"]
            ]
        return context
