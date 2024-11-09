from django import forms
from .models import RequestConfiguration, UserAPIKey, LanguageModel, ModelAPI
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML


class ParamsForm(forms.ModelForm):
    class Meta:
        model = RequestConfiguration
        fields = []

    temperature = forms.FloatField(label="Temperature", min_value=0.0, max_value=2.0)
    top_p = forms.FloatField(label="Top P", min_value=0.0, max_value=1.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("temperature", step="0.1"),
            Field("top_p", step="0.1"),
            Submit("submit", "Update Parameters"),
        )
        if self.instance and self.instance.params:
            self.fields["temperature"].initial = self.instance.params.get(
                "temperature", 1.0
            )
            self.fields["top_p"].initial = self.instance.params.get("top_p", 1.0)

    def save(self, commit=True):
        self.instance.params = {
            **(self.instance.params or {}),
            "temperature": self.cleaned_data["temperature"],
            "top_p": self.cleaned_data["top_p"],
        }
        return super().save(commit=commit)


class SystemPromptForm(forms.ModelForm):
    # system_prompt
    class Meta:
        model = RequestConfiguration
        fields = ["system_prompt"]

    system_prompt = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("system_prompt"),
            Submit("submit", "Update System Prompt"),
        )


class CreateAPIKeyForm(forms.ModelForm):
    # api
    # _key

    _key = forms.CharField(widget=forms.PasswordInput(), label="API Key")

    class Meta:
        model = UserAPIKey
        fields = ["api", "_key"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("api"),  # Then name field
            Field("_key"),  # Then key field
            Submit("submit", "Store API Key"),  # Submit button
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.key = self.cleaned_data["_key"]
        if commit:
            instance.save()
        return instance


class DeleteAPIKeyForm(forms.ModelForm):
    #
    class Meta:
        model = UserAPIKey
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                "<p>Are you sure you want to delete this API Key?</p>"
            ),  # Then name field
            Submit(
                "submit", "Delete API Key", css_class="btn btn-danger"
            ),  # Submit button
        )


class UpdateModelAPIForm(forms.ModelForm):
    # name
    # base_url

    class Meta:
        model = ModelAPI
        fields = ["name", "base_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("name"),  # Then name field
            Field("base_url"),  # Then base_url field
            Submit("submit", "Update API"),  # Submit button
        )


class RegisterModelAPIForm(forms.ModelForm):
    # identifier
    # name
    # base_url
    class Meta:
        model = ModelAPI
        fields = ["identifier", "name", "base_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("identifier"),  # Then identifier field
            Field("name"),  # Then name field
            Field("base_url"),  # Then base_url field
            Submit("submit", "Register API"),  # Submit button
        )


class DeleteModelAPIForm(forms.ModelForm):
    #
    class Meta:
        model = ModelAPI
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                "<p>Are you sure you want to delete this API? It will also delete the models from this API.</p>"
            ),  # Then name field
            Submit("submit", "Delete API", css_class="btn btn-danger"),  # Submit button
        )


class RegisterLanguageModelForm(forms.ModelForm):
    # name
    # context_window
    # api
    class Meta:
        model = LanguageModel
        fields = ["name", "context_window", "api"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("name"),  # Then name field
            Field("context_window"),  # Then context_window field
            Field("api"),  # Then api field
            Submit("submit", "Register Language Model"),  # Submit button
        )


class UpdateLanguageModelForm(forms.ModelForm):
    # name
    # context_window
    # api
    class Meta:
        model = LanguageModel
        fields = [
            "name",
            "context_window",
            "api",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("name"),  # Then name field
            Field("context_window"),  # Then context_window field
            Field("api"),  # Then api field
            Submit("submit", "Update Language Model"),  # Submit button
        )


class DeleteLanguageModelForm(forms.ModelForm):
    #
    class Meta:
        model = LanguageModel
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Delete Language Model"),  # Submit button
        )
