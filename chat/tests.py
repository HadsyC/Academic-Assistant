from django.test import TestCase
from django.contrib.auth.models import User
from .models import Chat, Message
from unittest.mock import patch, MagicMock
from services.models import LanguageModel, ModelAPI
from chat.views import yield_chat_response_stream


class ChatModelTests(TestCase):

    def test_user_creation(self):
        user = User.objects.create_user(username="testuser", password="password")
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "testuser")

    def test_chat_creation(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        self.assertIsInstance(chat, Chat)
        self.assertEqual(chat.topic, "Test Chat")
        self.assertEqual(chat.user, user)

    def test_message_creation(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        message = Message.objects.create(
            chat=chat,
            text="Hello, world!",
            sender="user",
            request_config=chat.request_config,
        )
        self.assertIsInstance(message, Message)
        self.assertEqual(message.text, "Hello, world!")
        self.assertEqual(message.chat, chat)

    def test_chat_str(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        self.assertEqual(str(chat), "Test Chat")

    def test_message_str(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        message = Message.objects.create(
            chat=chat,
            text="Hello, world!",
            sender="user",
            request_config=chat.request_config,
        )
        self.assertEqual(str(message), "Hello, world!")

    def test_update_chat_topic(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Initial Topic")
        chat.topic = "Updated Topic"
        chat.save()
        self.assertEqual(chat.topic, "Updated Topic")

    def test_delete_chat(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        chat_id = chat.id
        chat.delete()
        self.assertRaises(Chat.DoesNotExist, Chat.objects.get, id=chat_id)

    def test_chat_message_count(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        Message.objects.create(chat=chat, text="First message", sender="user")
        Message.objects.create(chat=chat, text="Second message", sender="user")
        self.assertEqual(chat.message_set.count(), 2)

    def test_assistant_message_count(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        Message.objects.create(chat=chat, text="Hello, world!", sender="user")
        Message.objects.create(
            chat=chat, text="How can I assist you?", sender="assistant"
        )
        self.assertEqual(chat.get_assistant_messages_count(), 1)

    def test_get_last_message(self):
        user = User.objects.create_user("testuser")
        chat = Chat.objects.create(user=user, topic="Test Chat")
        Message.objects.create(chat=chat, text="First message", sender="user")
        last_message = chat.get_last_message()
        self.assertEqual(last_message.text, "First message")


class YieldChatResponseStreamTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.model_api = ModelAPI.objects.create(
            identifier="test_api", name="Test API", base_url="https://api.test.com/"
        )
        self.language_model = LanguageModel.objects.create(
            name="test_model", api=self.model_api
        )
        self.chat = Chat.objects.create(user=self.user)
        self.message_to_populate = Message.objects.create(
            chat=self.chat, sender="waiting", text=""
        )
        self.messages = [{"role": "system", "content": "test system prompt"}]
        self.params = {"param1": "value1"}
        self.tools = [{"tool_name": "test_tool"}]
        self.tool_functions = {"get_file_text": lambda x: "file text"}

    @patch("chat.views.call_api")
    @patch("chat.views.process_response")
    @patch("chat.views.store_payload_and_usage")
    @patch("chat.views.handle_tools_calls")
    @patch("chat.views.finalize_stream")
    def test_yield_chat_response_stream(
        self,
        mock_finalize_stream,
        mock_handle_tools_calls,
        mock_store_payload_and_usage,
        mock_process_response,
        mock_call_api,
    ):
        mock_response = MagicMock()
        mock_call_api.return_value = mock_response
        mock_process_response.return_value = iter(
            [
                (
                    MagicMock(model_dump=lambda: {"chunk": "chunk1"}),
                    "generated_text_json1",
                    None,
                    "raw_text_generated1",
                ),
                (
                    MagicMock(model_dump=lambda: {"chunk": "chunk2"}),
                    "generated_text_json2",
                    None,
                    "raw_text_generated2",
                ),
            ]
        )

        generator = yield_chat_response_stream(
            message_to_populate=self.message_to_populate,
            messages=self.messages,
            language_model=self.language_model,
            user=self.user,
            params=self.params,
            tools=self.tools,
            tool_functions=self.tool_functions,
        )

        response_chunks = list(generator)

        self.assertEqual(
            response_chunks,
            [
                "data: generated_text_json1\n\n",
                "data: generated_text_json2\n\n",
                "event: close\n\n",
            ],
        )

        mock_call_api.assert_called_once_with(
            model=self.language_model,
            messages=self.messages,
            user=self.user,
            stream_flag=True,
            params=self.params,
            tools=self.tools,
        )

        mock_store_payload_and_usage.assert_called_once()
        mock_finalize_stream.assert_called_once_with(
            self.message_to_populate, "raw_text_generated2", self.messages
        )

    @patch("chat.views.call_api")
    @patch("chat.views.process_response")
    @patch("chat.views.store_payload_and_usage")
    @patch("chat.views.handle_tools_calls")
    @patch("chat.views.finalize_stream")
    def test_yield_chat_response_stream_with_tool_calls(
        self,
        mock_finalize_stream,
        mock_handle_tools_calls,
        mock_store_payload_and_usage,
        mock_process_response,
        mock_call_api,
    ):
        mock_response = MagicMock()
        mock_call_api.return_value = mock_response
        mock_process_response.side_effect = [
            iter(
                [
                    (
                        MagicMock(model_dump=lambda: {"chunk": "chunk1"}),
                        "generated_text_json1",
                        [{"tool": "call"}],
                        "raw_text_generated1",
                    )
                ]
            ),
            iter(
                [
                    (
                        MagicMock(model_dump=lambda: {"chunk": "chunk2"}),
                        "generated_text_json2",
                        None,
                        "raw_text_generated2",
                    )
                ]
            ),
        ]
        mock_handle_tools_calls.return_value = "tools_response"

        generator = yield_chat_response_stream(
            message_to_populate=self.message_to_populate,
            messages=self.messages,
            language_model=self.language_model,
            user=self.user,
            params=self.params,
            tools=self.tools,
            tool_functions=self.tool_functions,
        )

        response_chunks = list(generator)

        self.assertEqual(
            response_chunks,
            [
                "data: generated_text_json1\n\n",
                "data: generated_text_json2\n\n",
                "event: close\n\n",
            ],
        )

        mock_handle_tools_calls.assert_called_once_with(
            [{"tool": "call"}], self.tool_functions
        )
        mock_finalize_stream.assert_called_once_with(
            self.message_to_populate, "raw_text_generated2", self.messages
        )
