import django_tables2 as tables
from .models import ModelAPI, TokenUsage
from django.utils.safestring import mark_safe
import json


class UsageTable(tables.Table):
    created_at = tables.Column(
        accessor="payload_sent__created_at",
        verbose_name="Sent At",
    )
    prompt_tokens = tables.Column(
        accessor="prompt_tokens",
        verbose_name="Prompt Tokens",
        footer=lambda table: sum(x.prompt_tokens for x in table.data),
    )
    completion_tokens = tables.Column(
        accessor="completion_tokens",
        verbose_name="Completion Tokens",
        footer=lambda table: sum(x.completion_tokens for x in table.data),
    )

    prompt_cached_tokens = tables.Column(
        accessor="prompt_tokens_details.cached_tokens",
        verbose_name="Cached Tokens",
        footer=lambda table: sum(
            x.prompt_tokens_details.get("cached_tokens") for x in table.data
        ),
    )
    completion_reasoning_tokens = tables.Column(
        accessor="completion_tokens_details.reasoning_tokens",
        verbose_name="Reasoning Tokens",
        footer=lambda table: sum(
            x.completion_tokens_details.get("reasoning_tokens") for x in table.data
        ),
    )

    total_tokens = tables.Column(
        accessor="total_tokens",
        verbose_name="Total Tokens",
        footer=lambda table: sum(x.total_tokens for x in table.data),
    )

    class Meta:
        model = TokenUsage
        fields = (
            "payload_sent",
            "created_at",
            "prompt_tokens",
            "completion_tokens",
            "prompt_cached_tokens",
            "completion_reasoning_tokens",
            "total_tokens",
        )
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
            "style": "table-layout: fixed; width: 100%;",
        }

    def render_payload_sent(self, record):
        original_content = record.payload_sent.payload

        content = "\n---\n".join(
            [f"{c['role']}:\n\n{c['content']}" for c in original_content]
        )
        max_length = 50
        if len(content) > max_length:
            truncated_content = content[:max_length].rsplit(" ", 1)[0]
            short_content = truncated_content + "..."
        else:
            short_content = content

        record_id = record.payload_sent.id
        # Create a button that triggers a modal
        button_html = f"""
            <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#{record_id}Modal" title="View Payload">
                <i class="bi bi-file-text"></i>
            </button>
        """

        original_content = record.payload_sent.payload
        response = record.payload_sent.response

        # Iterate over the response
        if isinstance(response, dict):
            response_text = response["choices"][0]["message"]["content"]
        elif isinstance(response, list):
            content_parts = []
            fn_calls = False
            for r in response:
                if r["choices"]:
                    if delta_content := r["choices"][0]["delta"]["content"]:
                        content_parts.append(delta_content)
                    if tools_call := r["choices"][0]["delta"]["tool_calls"]:
                        fn_calls = True
                        for tc in tools_call:
                            if tc["function"]["name"]:
                                content_parts.append(tc["function"]["name"])
                            if tc["function"]["arguments"]:
                                content_parts.append(tc["function"]["arguments"])

            response_text = "".join(content_parts)
            if fn_calls:
                response_text = (
                    response_text.replace('{"', "(")
                    .replace('":', "=")
                    .replace("}", ")")
                    .replace(',"', ", ")
                )
            response_text = response_text.replace("\\n", "\n")
        else:
            raise ValueError("Response is not a list or dict")

        formatted_content = json.dumps(original_content, indent=4).replace("\\n", "\n")

        # Create the modal HTML
        modal_html = f"""
        <div class="modal fade" id="{record_id}Modal" tabindex="-1" aria-labelledby="{record_id}ModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
            <div class="modal-header">
                <h1 class="modal-title fs-5" id="{record_id}ModalLabel">Payload Content</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
                <div class="modal-body" style="text-align:left">
                    <pre>{formatted_content}</pre>
                    <h1 class="fs-5">Response</h1>
                    <pre>{response_text}</pre>
                </div>
            </div>
        </div>
        </div>
        """

        # Combine the button and modal HTML
        full_content = f"<div>{button_html}{modal_html}</div>"
        return mark_safe(full_content)

    def render_chat(self, record):
        redirect_url = f"/{record.payload_sent.chat.id}"
        return mark_safe(
            f'<a href="{redirect_url}">{record.payload_sent.chat.name}</a>'
        )


class ModelAPITable(tables.Table):
    edit = tables.Column(accessor="id", verbose_name="Edit", orderable=False)
    delete = tables.Column(accessor="id", verbose_name="Delete", orderable=False)

    class Meta:
        model = ModelAPI
        fields = ("name", "identifier", "base_url", "edit", "delete")
        attrs = {
            "class": "table table-responsive table-striped table-hover table-bordered table-sm text-center align-middle",
        }

    def render_edit(self, record):
        button = f"""
            <button type="button" class="btn btn-warning me-2" data-bs-toggle="modal" data-bs-target="#editModal{record.id}">
                <i class="bi bi-pencil"></i>
            </button>"""

        return mark_safe(button)

    def render_delete(self, record):
        button = f"""
            <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#deleteModal{record.id}">
                <i class="bi bi-trash"></i>
            </button>"""

        return mark_safe(button)
