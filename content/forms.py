from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML
from documents.forms import MultipleFileField
from services.models import LanguageModel
from .models import Quiz, Summary
from documents.models import ContextFile


class CreateQuizForm(forms.ModelForm):
    # files
    # selected_files
    # language_model
    # prompt

    # topic
    # difficulty
    # number_of_questions
    # points_per_question
    # options_per_question
    # time_limit

    files = MultipleFileField(required=False)
    selected_files = forms.ModelMultipleChoiceField(
        ContextFile.objects.all(), required=False
    )
    language_model = forms.ModelChoiceField(
        queryset=LanguageModel.objects.all(), initial=0
    )

    class Meta:
        model = Quiz
        fields = [
            "topic",
            "difficulty",
            "number_of_questions",
            "points_per_question",
            "options_per_question",
            "language_model",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("topic"),  # Title field
            Field("difficulty"),  # Difficulty field
            Field("number_of_questions"),  # Number of questions field
            Field("points_per_question"),  # Points per question field
            Field("options_per_question"),  # Options per question field
            Field("files"),  # Files field
            Field("selected_files"),  # Select files field
            Field("language_model"),  # Language model field
            Submit("submit", "Create Quiz"),  # Submit button
        )

    def clean(self):
        cleaned_data = super().clean()
        files = cleaned_data.get("files")
        select_files = cleaned_data.get("selected_files")

        if not files and not select_files:
            raise forms.ValidationError("You must select or upload files.")
        return cleaned_data


class QuestionForm(forms.Form):
    # answer

    answer = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(
        self, question, options, correct_option_index, explanations, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Set the available options for the question
        self.fields["answer"].choices = [
            (str(i), option) for i, option in enumerate(options)
        ]
        self.fields["answer"].label = question

        # Ensure the correct option index is stored as a string for comparison
        self.correct_option_index = str(correct_option_index)
        self.explanations = explanations

        # Configure the form layout using crispy-forms
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_id = "questionForm"
        self.helper.layout = Layout(
            Field("answer"),  # Crispy Forms layout for answer field
            # Submit("submit", "Submit"),  # Submit button
        )

    def clean(self):
        cleaned_data = super().clean()
        user_answer = cleaned_data.get("answer")

        # Compare user answer with the correct option index
        if user_answer != self.correct_option_index:
            raise forms.ValidationError(self.explanations[int(user_answer)])

        return cleaned_data

    def get_correct_explanation(self):
        return self.explanations[int(self.correct_option_index)]


class DeleteQuiz(forms.ModelForm):
    #
    class Meta:
        model = Quiz
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                """
                <p>Are you sure you want to delete this quizz?</p>
                """
            ),
            Submit("submit", "Delete Quiz"),
        )


class CreateSummaryForm(forms.ModelForm):
    # files
    # selected_files
    # language_model
    # prompt

    files = MultipleFileField(required=False)
    selected_files = forms.ModelMultipleChoiceField(
        queryset=ContextFile.objects.all(), required=False
    )
    language_model = forms.ModelChoiceField(
        queryset=LanguageModel.objects.all(), initial=0
    )

    class Meta:
        model = Summary
        fields = ["language_model"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # hidden
            Field("files"),  # Files field
            Field("selected_files"),  # Context files field
            Field("language_model"),  # Language model field
            Submit("submit", "Create Summary"),  # Submit button
        )

    def clean(self):
        cleaned_data = super().clean()
        files = cleaned_data.get("files")
        select_files = cleaned_data.get("selected_files")

        if not files and not select_files:
            raise forms.ValidationError("You must select or upload files.")
        return cleaned_data


class DeleteSummary(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<p>Are you sure you want to delete this summary?</p>"),
            Submit("submit", "Delete Summary"),
        )
