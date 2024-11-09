from django.urls import reverse
import django_tables2 as tables
from django.utils.safestring import mark_safe
from .models import Session, Plan


class PlanTable(tables.Table):
    view = tables.Column(
        accessor="id",
        verbose_name="View",
    )
    delete = tables.Column(
        accessor="id",
        verbose_name="Delete",
    )

    class Meta:
        model = Plan
        fields = (
            "plan_goal",
            "description",
            "start_date",
            "end_date",
            "all_done",
            "view",
            "delete",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_description(self, record):
        button = f"""
        <button type="button" class="btn btn-outline-info" data-bs-toggle="modal" data-bs-target="#description-{record.id}">
            <i class="bi bi-info-circle"></i>
        </button>"""
        modal = f"""
        <div class="modal fade" id="description-{record.id}" tabindex="-1" aria-labelledby="description-{record.id}-label" aria-hidden="true">
            <div class="modal-dialog modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="description-{record.id}-label">Description</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        {record.description}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>  
                </div>
            </div>
        </div>"""
        return mark_safe(button + modal)

    def render_view(self, record):
        url = reverse("plan_sessions", kwargs={"plan_id": record.id})
        modal_button = f"""
        <a href="{url}" class="btn btn-outline-warning">
            <i class="bi bi-file text"></i> <i class="bi bi-pen"></i>
        </a>"""
        return mark_safe(modal_button)

    def render_delete(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#delete-{record.id}">
            <i class="bi bi-trash"></i>
        </button>"""
        return mark_safe(modal_button)


class SessionTable(tables.Table):
    marked_done = tables.Column(
        accessor="marked_done",
        verbose_name="Done",
    )
    delete = tables.Column(
        accessor="id",
        verbose_name="Delete",
    )

    class Meta:
        model = Session
        fields = (
            "session_goal",
            "file_references",
            "date",
            "duration",
            "marked_done",
            "delete",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_delete(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#delete-{record.id}">
            <i class="bi bi-trash"></i>
        </button>"""
        return mark_safe(modal_button)

    def render_marked_done(self, record):
        checked = "checked" if record.marked_done else ""
        action_url = reverse("toggle_marked_done")

        form = (
            '<form action="' + action_url + '" method="get" style="display:inline;">'
            '<input type="hidden" name="record_id" value="' + str(record.id) + '">'
            '<input type="checkbox" class="form-check-input" '
            'name="marked_done" ' + checked + ' onchange="this.form.submit()">'
            "</form>"
        )

        return mark_safe(form)

    def render_file_references(self, record):
        modal_button = f"""
        <button type="button" class="btn btn-outline-info" data-bs-toggle="modal" data-bs-target="#file-{record.id}">
            {record.get_page_count()} pages
        </button>"""
        modal = f"""
        <div class="modal modal-xl fade text-start" id="file-{record.id}" tabindex="-1" aria-labelledby="file-{record.id}-label" aria-hidden="true">
            <div class="modal-dialog modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="file-{record.id}-label">File References</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body
                    ">
                        {record.get_full_text(in_html=True)}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>"""
        return mark_safe(modal_button + modal)
