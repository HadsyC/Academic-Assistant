from allauth.account.views import signup, login, logout
from django.urls import path

urlpatterns = [
    path("login/", login, name="account_login"),
    path("logout/", logout, name="account_logout"),
    path("signup/", signup, name="account_signup"),
]
