import json
import unittest
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from services.models import LanguageModel
from services.llm_handler import call_api, get_markdown, handle_tools_calls


class TestCallAPI(unittest.TestCase):
    @patch("services.llm_handler.OpenAI")
    @patch("services.llm_handler.UserAPIKey")
    def test_call_api(self, mock_user_api_key, mock_openai):
        # Setup mock objects
        mock_model = MagicMock(spec=LanguageModel)
        mock_model.api.identifier = "openai"
        mock_model.name = "test-model"
        mock_model.api.base_url = "https://api.openai.com"

        mock_user = MagicMock(spec=User)
        mock_user_api_key.objects.get.return_value.key = "test-api-key"

        mock_response = MagicMock()
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        params = {"temperature": 0.7}
        tools = [{"name": "tool1"}]

        # Call the function
        response = call_api(
            model=mock_model,
            messages=messages,
            user=mock_user,
            stream_flag=True,
            force_tool=True,
            params=params,
            tools=tools,
        )

        # Assertions
        self.assertEqual(response, mock_response)
        mock_user_api_key.objects.get.assert_called_once_with(
            user=mock_user, api__identifier="openai"
        )
        mock_openai.assert_called_once_with(
            api_key="test-api-key", base_url="https://api.openai.com"
        )
        mock_openai.return_value.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=messages,
            stream=True,
            temperature=0.7,
            stream_options={"include_usage": True},
            tools=tools,
            tool_choice="required",
        )


class TestHandleToolsCalls(unittest.TestCase):
    def setUp(self):
        self.tool_functions = {
            "function1": MagicMock(return_value="response1"),
            "function2": MagicMock(return_value="response2"),
        }

    def test_handle_tools_calls_single_call(self):
        tools_calls = {
            0: {
                "function": {
                    "name": "function1",
                    "arguments": json.dumps({"arg1": "value1"}),
                }
            }
        }
        response = handle_tools_calls(tools_calls, self.tool_functions)
        self.assertIn("response1", response)
        self.tool_functions["function1"].assert_called_once_with(arg1="value1")

    def test_handle_tools_calls_multiple_calls(self):
        tools_calls = {
            0: {
                "function": {
                    "name": "function1",
                    "arguments": json.dumps({"arg1": "value1"}),
                }
            },
            1: {
                "function": {
                    "name": "function2",
                    "arguments": json.dumps({"arg2": "value2"}),
                }
            },
        }
        response = handle_tools_calls(tools_calls, self.tool_functions)
        self.assertIn("response1", response)
        self.assertIn("response2", response)
        self.tool_functions["function1"].assert_called_once_with(arg1="value1")
        self.tool_functions["function2"].assert_called_once_with(arg2="value2")

    def test_handle_tools_calls_no_response(self):
        tools_calls = {
            0: {
                "function": {
                    "name": "function3",
                    "arguments": json.dumps({"arg1": "value1"}),
                }
            }
        }
        response = handle_tools_calls(tools_calls, self.tool_functions)
        self.assertIsNone(response)

    def test_handle_tools_calls_empty_calls(self):
        tools_calls = {}
        response = handle_tools_calls(tools_calls, self.tool_functions)
        self.assertIsNone(response)


class TestGetMarkdown(unittest.TestCase):
    def test_get_markdown_basic(self):
        text = "This is a **bold** text."
        expected_output = "<p>This is a <strong>bold</strong> text.</p>\n"
        result = get_markdown(text)
        self.assertEqual(result, expected_output)

    def test_get_markdown_with_code(self):
        text = "```python\nprint('Hello, world!')\n```"
        result = get_markdown(text)
        self.assertIn(
            '<div class="highlight"><pre><span></span><span class="nb">print</span><span class="p">(</span><span class="s1">&#39;Hello, world!&#39;</span><span class="p">)</span>\n</pre></div>\n',
            result,
        )

    def test_get_markdown_with_toc(self):
        text = ".. toc::\n\n# Title\n\n## Subtitle"
        result = get_markdown(text)
        self.assertIn('<div class="toc"', result)
        self.assertIn("<h3>Table of Contents</h3>", result)

    def test_get_markdown_with_math(self):
        text = "$$E = mc^2$$"
        result = get_markdown(text)
        self.assertIn('<span class="math">', result)
        self.assertIn("E = mc^2", result)

    def test_get_markdown_with_footnotes(self):
        text = "Here is a footnote reference[^1]\n\n[^1]: Here is the footnote."
        result = get_markdown(text)
        self.assertIn(
            '<p>Here is a footnote reference<sup class="footnote-ref" id="fnref-1"><a href="#fn-1">1</a></sup></p>\n<section class="footnotes">\n<ol>\n<li id="fn-1"><p>Here is the footnote.<a href="#fnref-1" class="footnote">&#8617;</a></p></li>\n</ol>\n</section>\n',
            result,
        )
