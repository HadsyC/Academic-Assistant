import django_tables2 as tables
from .models import ContextFile
from django.utils.safestring import mark_safe


class ContextFileTable(tables.Table):
    filename = tables.Column(
        accessor="filename",
        verbose_name="File Name",
    )
    uploaded_at = tables.Column(
        accessor="uploaded_at",
        verbose_name="Uploaded At",
    )
    processing_status = tables.Column(
        accessor="processing_status",
        verbose_name="Processing Status",
    )
    download = tables.Column(
        accessor="file",
        verbose_name="Download",
    )
    delete = tables.Column(
        accessor="id",
        verbose_name="Delete",
    )

    class Meta:
        model = ContextFile
        fields = (
            "filename",
            "uploaded_at",
            "processing_status",
            "processing_time",
            "token_amount",
            "download",
            "delete",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_download(self, value):
        return mark_safe(
            f'<a href="{value.url}" class="btn btn-success"><i class="bi bi-file-earmark-arrow-down"></i></a>'
        )

    def render_delete(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#delete-{record.id}">
            <i class="bi bi-trash"></i>
        </button>"""

        return mark_safe(modal_button)
