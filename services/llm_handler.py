from openai import OpenAI
import json
from services.models import (
    LanguageModel,
    PayloadSent,
    TokenUsage,
    UserAPIKey,
    _get_default_params,
)
from pygments import highlight
from pygments.lexers import get_lexer_by_name
import mistune
from pygments.formatters import html
import logging
from django.contrib.auth.models import User
from mistune.directives import RSTDirective, TableOfContents
from mistune.toc import render_toc_ul

logger = logging.getLogger("django.server")


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info, stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)
        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


def render_html_toc(renderer, title, collapse=False, **attrs):
    if not title:
        title = "Table of Contents"
    content = render_toc_ul(attrs["toc"])

    html = '<div class="toc"'
    if not collapse:
        html += " open"
    html += ">\n<h3>" + title + "</h3>\n"
    return html + content + "</div>\n"


class MyTableOfContents(TableOfContents):
    def __call__(self, directive, md):
        if md.renderer and md.renderer.NAME == "html":
            # only works with HTML renderer
            directive.register("toc", self.parse)
            md.before_render_hooks.append(self.toc_hook)
            md.renderer.register("toc", render_html_toc)


def get_markdown(text):
    markdown = mistune.create_markdown(
        renderer=HighlightRenderer(),
        plugins=[
            "strikethrough",
            "footnotes",
            "table",
            "url",
            "task_lists",
            "def_list",
            "abbr",
            "mark",
            "insert",
            "superscript",
            "subscript",
            "math",
            "spoiler",
            RSTDirective([MyTableOfContents()]),
        ],
    )
    return markdown(text)


def call_api(
    model: LanguageModel,
    messages: list[dict],
    user: User,
    stream_flag: bool = False,
    force_tool: bool = False,
    params: dict = _get_default_params(),
    tools: list[dict] = None,
):
    logger.warning(f"Calling API for model: {model.name}")
    api_identifier = model.api.identifier
    kwargs = {
        "model": model.name,
        "messages": messages,
        "stream": stream_flag,
        **params,
    }
    if stream_flag and api_identifier == "openai":
        kwargs["stream_options"] = {"include_usage": True}

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if force_tool:
        kwargs["tool_choice"] = "any" if api_identifier == "mistral" else "required"

    api_key = UserAPIKey.objects.get(user=user, api__identifier=api_identifier).key
    response = OpenAI(
        api_key=api_key,
        base_url=model.api.base_url,
    ).chat.completions.create(**kwargs)
    logger.warning("API responded")
    return response


def update_tool_calls(tool_call, tool_calls):
    """Update the tool calls dictionary with new tool call information."""
    index = tool_call.index
    tool_calls[index] = tool_calls.get(
        index,
        {"id": None, "function": {"arguments": "", "name": ""}, "type": "function"},
    )

    if tool_call.id:
        tool_calls[index]["id"] = tool_call.id
    if tool_call.function.name:
        tool_calls[index]["function"]["name"] = tool_call.function.name
    tool_calls[index]["function"]["arguments"] += tool_call.function.arguments

    return tool_calls


def process_chunk(chunk, raw_text_generated, tool_calls):
    """Process each chunk to extract text and tool call information."""
    generated_text_json = None  # Initialize data to None
    if chunk.choices:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            raw_text_generated += delta.content
            marked = get_markdown(raw_text_generated)
            generated_text_json = json.dumps({"text": marked})
        if delta and delta.tool_calls:
            tool_calls = update_tool_calls(delta.tool_calls[0], tool_calls)

    return raw_text_generated, generated_text_json, tool_calls


def process_response(response):
    """Process the response stream, yielding text and tool calls."""
    raw_text_generated = ""
    tool_calls = {}
    for chunk in response:
        raw_text_generated, generated_text_json, tool_calls = process_chunk(
            chunk, raw_text_generated, tool_calls
        )
        yield chunk, generated_text_json, tool_calls, raw_text_generated


def handle_tools_calls(tools_calls: dict, tool_functions: list[dict]) -> str:
    """Handle tool calls and return the response."""
    tool_responses = []
    for tool_call in tools_calls.values():
        function_name = tool_call["function"]["name"]
        function_arguments = json.loads(tool_call["function"]["arguments"])
        if function_name in tool_functions:
            args = json.dumps(function_arguments, indent=4)
            logger.warning(f"Calling function: {function_name}\nArguments:\n{args}")
            _tool_response = tool_functions[function_name](**function_arguments)
            if _tool_response:
                tool_response = f"Response for {function_name} with args {function_arguments}:\n{_tool_response}"
                tool_responses.append(tool_response)
    if tool_responses:
        full_response = "\n".join(tool_responses)
        return full_response
    return None


def store_payload_and_usage(messages, chunk_responses, request_config, user):
    """Handle the payload and log the response."""
    payload_sent = PayloadSent.objects.create(
        request_config=request_config,
        payload=messages,
        user=user,
        response=chunk_responses,
    )
    usage_data = chunk_responses[-1]["usage"]
    TokenUsage.objects.create(payload_sent=payload_sent, **usage_data)
