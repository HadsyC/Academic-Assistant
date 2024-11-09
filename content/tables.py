from django.urls import reverse
import django_tables2 as tables

from documents.models import ContextFile
from .models import Quiz, Summary
from django.utils.safestring import mark_safe


class QuizTable(tables.Table):
    view = tables.Column(
        accessor="id",
        verbose_name="Take Quiz",
    )
    delete = tables.Column(
        accessor="id",
        verbose_name="Delete",
    )

    class Meta:
        model = Quiz
        fields = (
            "topic",
            "difficulty",
            "number_of_questions",
            "points_per_question",
            "processing_status",
            "view",
            "delete",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_view(self, record):
        url = reverse("quizz_details", kwargs={"quizz_id": record.id})
        modal_button = f"""
        <a href="{url}" class="btn btn-outline-warning">
            <i class="bi bi-file-text"></i> <i class="bi bi-pen"></i>
        </a>"""
        return mark_safe(modal_button)

    def render_delete(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#delete-{record.id}">
            <i class="bi bi-trash"></i>
        </button>"""
        return mark_safe(modal_button)


class SummaryTable(tables.Table):
    context_files = tables.Column(
        accessor="context_files",
        verbose_name="Context Files",
    )
    view = tables.Column(
        accessor="id",
        verbose_name="View",
    )
    delete = tables.Column(
        accessor="id",
        verbose_name="Delete",
    )

    class Meta:
        model = Summary
        fields = (
            "topic",
            "context_files",
            "processing_status",
            "view",
            "delete",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_context_files(self, record):
        context_files = record.context_files.all()
        return ", ".join([file.filename for file in context_files])

    def render_view(self, record):
        url = reverse("summary_details", kwargs={"summary_id": record.id})
        modal_button = f"""
        <a href="{url}" class="btn btn-outline-warning">
            <i class="bi bi-file text"></i> <i class="bi bi-eye"></i>
        </a>"""
        return mark_safe(modal_button)

    def render_delete(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#delete-{record.id}">
            <i class="bi bi-trash"></i>
        </button>"""
        return mark_safe(modal_button)
