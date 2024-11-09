from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML

from services.models import LanguageModel, get_default_language_model
from .models import ContextFile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class FileUploadForm(forms.Form):
    files = MultipleFileField()
    language_model = forms.ModelChoiceField(
        queryset=LanguageModel.objects.all(), initial=0
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("files"),  # Files field
            Field("language_model"),  # Language model field
            Submit("submit", "Add Files"),  # Submit button
        )


class FileUploadOrSelectForm(forms.Form):
    uploaded_files = MultipleFileField(required=False)
    selected_files = forms.ModelMultipleChoiceField(
        queryset=ContextFile.objects.all(), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("uploaded_files"),  # File field for upload
            Field("selected_files"),  # File selection field
            Submit("submit", "Add Files"),  # Submit button
        )

    def validate_files(self):
        files = self.cleaned_data.get("files")
        selected_files = self.cleaned_data.get("selected_files")
        if not files and not selected_files:
            raise forms.ValidationError("You must select or upload files.")
        return self.cleaned_data


class FileDeleteForm(forms.ModelForm):
    class Meta:
        model = ContextFile
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<p>Are you sure you want to delete this file?</p>"),
            Submit("submit", "Delete File"),
        )
