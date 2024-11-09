from django import forms
from .models import Chat
from services.models import UserAPIKey, LanguageModel
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from crispy_forms.bootstrap import FieldWithButtons


class UpdateChatForm(forms.ModelForm):
    # topic
    class Meta:
        model = Chat
        fields = ["topic"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("topic"),  # Then name field
            Submit("submit", "Rename Chat"),  # Submit button
        )


class DeleteChatForm(forms.ModelForm):
    #
    class Meta:
        model = Chat
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<p>Are you sure you want to delete this chat?</p>"),  # Text
            Submit("submit", "Delete Chat"),  # Submit button
        )


class MessageForm(forms.Form):
    # language_model
    # text
    language_model = forms.ModelChoiceField(
        queryset=LanguageModel.objects.all(), initial=0
    )
    text = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Ask something about your material..."}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(Field("language_model"), css_class="col-auto"),
                    Div(
                        FieldWithButtons(
                            "text",
                            Submit("submit", "Send"),
                        ),
                        css_class="col",
                    ),
                    css_class="row",
                ),
                css_class="container-fluid",
            ),
        )
