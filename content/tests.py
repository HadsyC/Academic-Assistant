import os
from django.test import TestCase
from django.contrib.auth.models import User

from content.signals import create_question
from .models import Quiz, Question, Option, Summary, ContextFile
from django.core.files.uploadedfile import SimpleUploadedFile


class ContentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

        # Ensure the mediafiles directory exists
        self.media_dir = os.path.join("mediafiles")
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)

        # Create a test file if it does not exist
        self.test_file_path = os.path.join(self.media_dir, "test_file.txt")
        if not os.path.isfile(self.test_file_path):
            with open(self.test_file_path, "w") as f:
                f.write("This is a test file content.")

        self.file = SimpleUploadedFile("test_file.txt", b"This is a test file content.")
        self.context_file = ContextFile.objects.create(
            filename="test_file.txt",
            user=self.user,
            full_text="This is a test file.",
            processing_status="complete",
            file=self.file,
        )
        self.quiz = Quiz.objects.create(
            topic="Test Quiz",
            difficulty="medium",
            number_of_questions=5,
            points_per_question=1,
            options_per_question=4,
            user=self.user,
        )

    def test_quiz_creation(self):
        self.assertEqual(self.quiz.topic, "Test Quiz")
        self.assertEqual(self.quiz.difficulty, "medium")
        self.assertEqual(self.quiz.number_of_questions, 5)
        self.assertEqual(self.quiz.options_per_question, 4)

    def test_quiz_str(self):
        self.assertEqual(str(self.quiz), "Test Quiz")

    def test_quiz_total_points(self):
        self.assertEqual(self.quiz.total_points, 5)

    def test_question_creation(self):
        question = Question.objects.create(quiz=self.quiz, question="What is a test?")
        self.assertEqual(question.question, "What is a test?")
        self.assertEqual(question.quiz, self.quiz)

    def test_question_str(self):
        question = Question.objects.create(quiz=self.quiz, question="What is a test?")
        self.assertEqual(str(question), "What is a test?")

    def test_option_creation(self):
        question = Question.objects.create(quiz=self.quiz, question="What is a test?")
        Option.objects.create(question=question, option="Option 1", is_correct=True)
        self.assertEqual(question.option_set.count(), 1)

    def test_summary_creation(self):
        summary = Summary.objects.create(
            text="This is a test summary text", user=self.user
        )
        self.assertEqual(summary.text, "This is a test summary text")
        self.assertEqual(summary.user, self.user)

    def test_summary_topic(self):
        summary = Summary.objects.create(topic="Summary Text", user=self.user)
        self.assertEqual(str(summary), "Summary Text")

    def test_context_file_creation(self):
        self.assertEqual(self.context_file.filename, "test_file.txt")
        self.assertEqual(self.context_file.full_text, "This is a test file.")
        self.assertEqual(self.context_file.user, self.user)
        self.assertIsNotNone(self.context_file.file)  # Ensure the file is associated
        self.assertEqual(self.context_file.file.read(), b"This is a test file content.")

    def test_context_file_str(self):
        self.assertEqual(str(self.context_file), "test_file.txt")

    def test_context_file_retrieval(self):
        context_file = ContextFile.objects.get(id=self.context_file.id)
        self.assertIsNotNone(context_file)
        self.assertEqual(context_file.filename, "test_file.txt")

    def test_save_summary_with_context_files(self):
        summary = Summary.objects.create(text="Summary Text", user=self.user)
        summary.context_files.add(self.context_file)
        self.assertIn(self.context_file, summary.context_files.all())

    def test_context_file_file_field(self):
        self.assertEqual(self.context_file.filename, "test_file.txt")
        self.assertTrue(
            self.context_file.file.storage.exists(self.context_file.file.name)
        )  # Check if file exists

    def test_context_file_file_content(self):
        with self.context_file.file.open("rb") as f:
            content = f.read()
            self.assertEqual(content, b"This is a test file content.")


class CreateQuestionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.quiz = Quiz.objects.create(
            user=self.user,
            topic="Sample Quiz",
            difficulty="Easy",
            number_of_questions=5,
            options_per_question=4,
            points_per_question=10,
        )

    def test_create_question(self):
        question_text = "What is the capital of France?"
        options = ["Paris", "London", "Berlin", "Madrid"]
        correct_option_index = 0
        explanations = [
            "Paris is the capital of France.",
            "London is the capital of the UK.",
            "Berlin is the capital of Germany.",
            "Madrid is the capital of Spain.",
        ]

        create_question(
            quizz_id=self.quiz.id,
            question_text=question_text,
            options=options,
            correct_option_index=correct_option_index,
            explanations=explanations,
        )

        question = Question.objects.get(quiz=self.quiz, question=question_text)
        self.assertIsNotNone(question)
        self.assertEqual(question.question, question_text)

        options = Option.objects.filter(question=question)
        self.assertEqual(len(options), 4)

        for i, option in enumerate(options):
            self.assertEqual(option.option, options[i].option)
            self.assertEqual(option.explanation, explanations[i])
            self.assertEqual(option.is_correct, i == correct_option_index)
