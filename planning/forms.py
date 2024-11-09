from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML
from documents.forms import MultipleFileField
from services.models import LanguageModel
from documents.models import ContextFile
from .models import Plan, Session


class DateInput(forms.DateInput):
    input_type = "date"


class CreatePlanForm(forms.ModelForm):
    # files
    # selected_files
    # language_model
    # prompt

    # plan_goal
    # start
    # end

    plan_goal = forms.CharField()
    files = MultipleFileField(required=False)
    selected_files = forms.ModelMultipleChoiceField(
        ContextFile.objects.all(), required=False
    )
    language_model = forms.ModelChoiceField(
        queryset=LanguageModel.objects.all(), initial=0
    )
    start_date = forms.DateField(widget=DateInput)
    end_date = forms.DateField(widget=DateInput)

    class Meta:
        model = Plan
        fields = [
            "plan_goal",
            "start_date",
            "end_date",
            "files",
            "selected_files",
            "language_model",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("plan_goal"),  # Plan goal field
            Field("start_date"),  # Start field
            Field("end_date"),  # End field
            Field("files"),  # Files field
            Field("selected_files"),  # Select files field
            Field("language_model"),  # Language model field
            Submit("submit", "Create Plan"),  # Submit button
        )


class DeletePlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "deletePlanForm"
        self.helper.layout = Layout(
            HTML("<p>Are you sure you want to delete this plan?</p>"),
            Submit("submit", "Delete Plan"),
        )


class DeleteSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<p>Are you sure you want to delete this session?</p>"),
            Submit("submit", "Delete Session"),
        )


class MarkDoneSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["marked_done"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("marked_done"),
            HTML("<p>Mark this session as done?</p>"),
            Submit("submit", "Mark Done"),
        )
