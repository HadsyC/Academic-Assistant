from django.urls import path
from . import views

urlpatterns = [
    path("apis", views.ModelAPIListView.as_view(), name="apis"),
    path("create_api/", views.create_api, name="create_api"),
    path("update_api/<int:api_id>", views.update_api, name="update_api"),
    path("delete_api/<int:api_id>", views.delete_api, name="delete_api"),
    path(
        "language_models", views.LanguageModelListView.as_view(), name="language_models"
    ),
    path(
        "create_language_model",
        views.create_language_model,
        name="create_language_model",
    ),
    path(
        "update_language_model/<int:language_model_id>",
        views.update_language_model,
        name="update_language_model",
    ),
    path(
        "delete_language_model/<int:language_model_id>",
        views.delete_language_model,
        name="delete_language_model",
    ),
    path("usage/", views.UsageListView.as_view(), name="usage"),
    path("api_keys/", views.api_keys, name="api_keys"),
    path("create_api_key/", views.create_api_key, name="create_api_key"),
    path("delete_api_key/<int:key_id>", views.delete_api_key, name="delete_api_key"),
    path(
        "update_params/<int:request_config_id>",
        views.update_params,
        name="update_params",
    ),
    path(
        "update_system_prompt/<int:request_config_id>",
        views.update_system_prompt,
        name="update_system_prompt",
    ),
]
