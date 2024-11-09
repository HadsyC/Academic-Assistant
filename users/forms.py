from allauth.account.forms import SignupForm, LoginForm

# from django import forms
from django.contrib.auth.models import User


class MyCustomSignupForm(SignupForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("email")

    def save(self, request):
        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(MyCustomSignupForm, self).save(request)

        # Add your own processing here.
        user.save()

        # You must return the original result.
        return user


class MyCustomLoginForm(LoginForm):
    class Meta:
        model = User
        fields = ("username", "password")

    def __init__(self, *args, **kwargs):
        super(MyCustomLoginForm, self).__init__(*args, **kwargs)
        self.fields["password"].help_text = None

    def save(self, request):
        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(MyCustomLoginForm, self).save(request)

        # Add your own processing here.
        user.save()

        # You must return the original result.
        return user
