import os
from datetime import datetime, timedelta, date
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Plan, Session
from documents.models import ContextFile, FileReference
from django.core.files.uploadedfile import SimpleUploadedFile


class PlanningModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

        # Ensure the mediafiles/planning directory exists
        self.media_dir = os.path.join("mediafiles", "planning")
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)

        # Create a test file if it does not exist
        self.test_file_path = os.path.join(self.media_dir, "test_document.txt")
        if not os.path.isfile(self.test_file_path):
            with open(self.test_file_path, "w") as f:
                f.write("This is a test document content.")

        # Create a context file instance
        with open(self.test_file_path, "rb") as f:
            self.file = SimpleUploadedFile("test_document.txt", f.read())
            self.context_file = ContextFile.objects.create(
                filename="test_document.txt",
                user=self.user,
                full_text="This is a test document.",
                processing_status="completed",
                file=self.file,
            )
            self.file_reference = FileReference.objects.create(
                context_file=self.context_file, start_page_index=0, end_page_index=0
            )

        # Create a Plan instance with parsed dates
        self.plan = Plan.objects.create(
            plan_goal="Test Plan Goal",
            description="This is a test plan description.",
            user=self.user,
            start_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
            end_date=datetime.strptime("2023-12-31", "%Y-%m-%d"),
        )

        # Create a Session instance associated with the plan
        self.session = Session.objects.create(
            plan=self.plan,
            session_goal="Test Session Goal",
            date=date(2023, 6, 1),
            duration=timedelta(hours=1),
        )

    def test_plan_creation(self):
        self.assertEqual(self.plan.plan_goal, "Test Plan Goal")
        self.assertEqual(self.plan.description, "This is a test plan description.")
        self.assertEqual(self.plan.user, self.user)

    def test_plan_str(self):
        self.assertEqual(str(self.plan), "Test Plan Goal")

    def test_session_creation(self):
        self.assertEqual(self.session.session_goal, "Test Session Goal")
        self.assertEqual(self.session.plan, self.plan)
        self.assertEqual(
            str(self.session.date.strftime("%Y-%m-%d")), "2023-06-01"
        )  # Ensure date is correctly formatted

    def test_session_str(self):
        self.assertEqual(str(self.session), "Test Session Goal")

    def test_plan_session_relationship(self):
        self.assertIn(self.session, self.plan.session_set.all())

    def test_plan_total_sessions(self):
        self.assertEqual(
            self.plan.total_sessions, 1
        )  # Verify that there's one session in the plan

    def test_context_file_creation(self):
        self.assertEqual(self.context_file.filename, "test_document.txt")
        self.assertIsNotNone(self.context_file.file)  # Ensure the file is associated

    def test_context_file_str(self):
        self.assertEqual(str(self.context_file), "test_document.txt")

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

    def test_processing_done_property(self):
        self.session.file_references.add(self.file_reference)
        self.assertFalse(
            self.plan.processing_done
        )  # Only validates if there is still a session that isn't done
