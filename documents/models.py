from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import os

from services.llm_handler import get_markdown


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # Get the file extension
    valid_extensions = [".pdf", ".txt"]
    if ext.lower() not in valid_extensions:
        raise ValidationError(
            "Unsupported file extension. Only .pdf and .txt files are allowed."
        )


def validate_file_size(value):
    max_size = 25 * 1024 * 1024  # 25MB
    if value.size > max_size:
        raise ValidationError("File too large. Size should not exceed 25 MB.")


def user_directory_path(instance, filename):
    username = instance.user.username
    return f"{username}/{filename}"


class ContextFile(models.Model):
    file = models.FileField(
        upload_to=user_directory_path,
        validators=[validate_file_extension, validate_file_size],
    )
    full_text = models.TextField(blank=True, null=True)
    markdown_json = models.JSONField(blank=True, null=True)
    token_amount = models.IntegerField(blank=True, null=True)
    processing_status = models.CharField(max_length=20, default="pending")
    processing_time = models.DurationField(blank=True, null=True)
    filename = models.CharField(max_length=100, blank=True, null=True)
    html = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

    def get_paginated_text(self):
        total_pages = self.markdown_json[0]["metadata"]["page_count"]
        text = f"Filename: {self.filename}, Total pages:({total_pages})\n"
        for page in self.markdown_json:
            text += f"[Page {page['metadata']['page']}]:\n"
            text += page["text"]
        return text

    def get_html_content(self):
        return f"{self.filename}:\n{self.html}"

    def get_pages(self, start_page, end_page, in_html=False):
        text = f"Pages {start_page} to {end_page} from {self.filename}:\n"
        html = get_markdown(text)
        for page in self.markdown_json:
            if (
                page["metadata"]["page"] >= start_page
                and page["metadata"]["page"] <= end_page
            ):
                text += f"[Page {page['metadata']['page']}]:\n{page['text']}"
                html += get_markdown(
                    f"[Page {page['metadata']['page']}]:\n{page['text']}"
                )
        if in_html:
            return html
        return text

    def get_full_text(self):
        return f"{self.filename}:\n{self.full_text}"


class FileReference(models.Model):
    context_file = models.ForeignKey(ContextFile, on_delete=models.CASCADE)
    start_page_index = models.PositiveIntegerField()
    end_page_index = models.PositiveIntegerField()

    def get_reference_text(self, in_html=False):
        return self.context_file.get_pages(
            self.start_page_index, self.end_page_index, in_html
        )
