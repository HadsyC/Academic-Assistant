import os
from django.test import TestCase
from django.contrib.auth.models import User
from .models import ContextFile
from django.core.files.uploadedfile import SimpleUploadedFile


class DocumentsModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

        # Ensure the mediafiles/documents directory exists
        self.media_dir = os.path.join("mediafiles", "documents")
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)

        # Create a test file if it does not exist
        self.test_file_path = os.path.join(self.media_dir, "test_document.txt")
        if not os.path.isfile(self.test_file_path):
            with open(self.test_file_path, "w") as f:
                f.write("This is a test document content.")

        # Create an instance of ContextFile with the test file
        with open(self.test_file_path, "rb") as f:
            self.file = SimpleUploadedFile("test_document.txt", f.read())
            self.context_file = ContextFile.objects.create(
                filename="test_document.txt",
                user=self.user,
                full_text="This is a test document.",
                processing_status="complete",
                file=self.file,
            )

    def test_context_file_creation(self):
        self.assertEqual(self.context_file.filename, "test_document.txt")
        self.assertEqual(self.context_file.full_text, "This is a test document.")
        self.assertEqual(self.context_file.user, self.user)
        self.assertIsNotNone(self.context_file.file)  # Ensure the file is associated

    def test_context_file_str(self):
        self.assertEqual(str(self.context_file), "test_document.txt")

    def test_context_file_retrieval(self):
        context_file = ContextFile.objects.get(id=self.context_file.id)
        self.assertIsNotNone(context_file)
        self.assertEqual(context_file.filename, "test_document.txt")

    def test_context_file_file_existence(self):
        self.assertTrue(
            os.path.isfile(self.test_file_path)
        )  # Check if the test file exists

    def test_context_file_file_content(self):
        with open(self.test_file_path, "rb") as f:
            content = f.read()
            self.assertEqual(
                content, b"This is a test document content."
            )  # Ensure content matches

    def test_context_file_file_read(self):
        file_contents = self.context_file.get_full_text()
        self.assertIn("test_document.txt:\nThis is a test document.", file_contents)

    def test_context_file_html_output(self):
        self.context_file.html = "<p>This is a test document in HTML format.</p>"
        self.context_file.save()
        self.assertEqual(
            self.context_file.html, "<p>This is a test document in HTML format.</p>"
        )
