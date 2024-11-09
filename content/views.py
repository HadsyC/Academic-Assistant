import threading
from django.shortcuts import redirect, render
from documents.signals import process_files
from services.models import get_default_request_config
from .models import BaseProcessModel, Question, Quiz, Option, Score, Summary
from .forms import (
    CreateQuizForm,
    CreateSummaryForm,
    DeleteQuiz,
    DeleteSummary,
    QuestionForm,
)
from .signals import (
    check_files_ready_signal,
)
from documents.models import ContextFile
from django.contrib import messages as django_messages
import os
from django_tables2 import SingleTableView
from .tables import QuizTable, SummaryTable  # Add this import statement
from datetime import datetime


def base(request):
    return render(request, "content/content.html")


def signal_files_ready(context_files, instance):
    process_files(context_files, instance.request_config.language_model.name)
    check_files_ready_signal(context_files, instance)


def process_uploaded_files(uploaded_files, instance: BaseProcessModel):
    new_context_files = []
    for file in uploaded_files:
        new_file = ContextFile(
            file=file, user=instance.user, filename=os.path.basename(file.name)
        )
        new_file.save()
        new_context_files.append(new_file)

    instance.context_files.set(new_context_files)
    if not instance.request_config:
        instance.request_config = get_default_request_config()
        instance.save()

    thread = threading.Thread(
        target=signal_files_ready,
        args=(new_context_files, instance),
    )
    thread.start()


def process_selected_files(selected_files, instance: BaseProcessModel):
    instance.context_files.set(selected_files)
    thread = threading.Thread(
        target=check_files_ready_signal, args=(selected_files, instance)
    )
    thread.start()


def create_quiz(request):
    if request.method == "POST":
        form = CreateQuizForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            form.instance.user = user
            uploaded_files = form.cleaned_data.get("files")
            selected_files = form.cleaned_data.get("selected_files")
            quiz: Quiz = form.save()
            if uploaded_files:
                process_uploaded_files(uploaded_files, quiz)
            if selected_files:
                process_selected_files(selected_files, quiz)

            if not uploaded_files and not selected_files:
                quiz.delete()
        else:
            django_messages.error(request, form.errors)
    return redirect("quizzes")


def delete_quiz(request, quizz_id):
    if request.method == "POST":
        quiz = Quiz.objects.get(id=quizz_id)
        quiz.delete()
    return redirect("quizzes")


def summaries(request):
    return render(request, "content/summaries.html")


def construct_question_form(
    question, curr_question=None, form=None, data=None, prefix=None
):
    if curr_question:
        if curr_question.id == question.id:
            return form

    options = Option.objects.filter(question=question)
    correct_option = options.get(is_correct=True).option
    explanations = [option.explanation for option in options]
    options = [option.option for option in options]
    correct_index = options.index(correct_option)

    form = QuestionForm(
        question=question.question,
        options=options,
        correct_option_index=correct_index,
        explanations=explanations,
        data=data,  # Pass POST data for form validation
        prefix=prefix,  # Pass the prefix to ensure unique field names
    )
    return form


def evaluate_quiz(question_forms, questions):
    score = 0
    answers = []
    for idx, question_form in enumerate(question_forms):
        question = questions[idx]
        options = Option.objects.filter(question=question)
        form_valid = question_form.is_valid()
        selected_index = int(question_form.cleaned_data["answer"])
        answers.append(options[selected_index])
        if form_valid:
            correct_list = [opt.is_correct for opt in options]
            points_per_question = question.quiz.points_per_question
            answer_correct = correct_list[selected_index]
            if answer_correct:
                score += points_per_question
    return score, answers


def score_details(request, score_id):
    score = Score.objects.get(id=score_id)
    return render(request, "content/score_details.html", {"score": score})


class QuizListView(SingleTableView):
    model = Quiz
    table_class = QuizTable
    template_name = "content/quizzes.html"
    context_object_name = "quizzes"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        queryset = Quiz.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_quizz_form"] = CreateQuizForm()
        context["delete_forms"] = [
            DeleteQuiz(instance=quiz) for quiz in context["quizzes"]
        ]
        return context


def quiz_details(request, quizz_id, start_time=None):
    quiz = Quiz.objects.get(id=quizz_id)
    questions = Question.objects.filter(quiz=quiz)
    context = {"quiz": quiz}
    question_forms = []
    if request.method == "POST":

        for idx, question in enumerate(questions):
            form = construct_question_form(
                question,
                data=request.POST,  # Pass POST data for validation
                prefix=f"q{idx}",  # Unique prefix for each form
            )
            question_forms.append(form)

        # from start_time|date "Y-m-d H:i:s"
        start_time_str = request.POST.get("start_time")
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        time_taken = datetime.now() - start_time
        score, answers = evaluate_quiz(question_forms, questions)
        score_model = Score.objects.create(
            quiz=quiz,
            score=score,
            time_taken=time_taken,
        )
        score_model.answers.set(answers)
        score_model.save()
        return redirect("score_details", score_id=score_model.id)

    else:
        context["start_time"] = datetime.now()
        for idx, question in enumerate(questions):
            form = construct_question_form(
                question, prefix=f"q{idx}"  # Unique prefix for each form
            )
            question_forms.append(form)

    context["questions_forms"] = question_forms
    return render(request, "content/quiz_details.html", context)


def create_summary(request):
    if request.method == "POST":
        form = CreateSummaryForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_files = form.cleaned_data.get("files")
            selected_files = form.cleaned_data.get("selected_files")
            form.instance.user = request.user
            form.instance.text = ""  # generate summary here
            form.instance.topic = ""
            form.save()
            if uploaded_files:
                process_uploaded_files(uploaded_files, form.instance)
            if selected_files:
                process_selected_files(selected_files, form.instance)

            if not uploaded_files and not selected_files:
                form.instance.delete()

        else:
            django_messages.error(request, form.errors)
    return redirect("summaries")


def delete_summary(request, summary_id):
    if request.method == "POST":
        summary = Summary.objects.get(id=summary_id)
        summary.delete()
    return redirect("summaries")


class SummaryListView(SingleTableView):
    model = Summary
    table_class = SummaryTable
    template_name = "content/summaries.html"
    context_object_name = "summaries"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        queryset = Summary.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_summary_form"] = CreateSummaryForm()
        context["delete_forms"] = [
            DeleteSummary(instance=summary) for summary in context["summaries"]
        ]
        return context


def summary_details(request, summary_id):
    summary = Summary.objects.get(id=summary_id)
    return render(request, "content/summary_details.html", {"summary": summary})
