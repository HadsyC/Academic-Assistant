from datetime import timedelta
from django.db import models
from django.db.models import Sum
from chat.models import BaseContentModel
from services.models import RequestConfiguration
from documents.models import ContextFile


class BaseProcessModel(BaseContentModel):
    request_config = models.ForeignKey(
        RequestConfiguration, on_delete=models.CASCADE, null=True, blank=True
    )  # null necessary for complex models like summaries that need to be created before the request config
    context_files = models.ManyToManyField(ContextFile, blank=True)
    processing_status = models.CharField(max_length=20, default="pending")

    @property
    def total_files(self):
        return self.context_files.count()

    @property
    def total_tokens(self):
        return self.context_files.aggregate(Sum("token_amount"))["token_amount__sum"]

    @property
    def processing_done(self):
        if self.context_files.count() == 0:
            return False
        return all(
            [file.processing_status == "completed" for file in self.context_files.all()]
        )

    @property
    def total_processing_time(self):
        # Aggregate the sum of processing_time across related context_files
        total_time = self.context_files.aggregate(Sum("processing_time"))[
            "processing_time__sum"
        ]
        return total_time if total_time else timedelta(0)


class Summary(BaseProcessModel):
    class Meta:
        verbose_name_plural = "Summaries"

    text = models.TextField()
    html = models.TextField(blank=True, null=True)


class Quiz(BaseProcessModel):
    class Meta:
        verbose_name_plural = "Quizzes"

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="medium"
    )
    number_of_questions = models.PositiveIntegerField(default=5)
    points_per_question = models.PositiveIntegerField(default=1)
    options_per_question = models.PositiveIntegerField(default=4)

    @property
    def actual_total_questions(self):
        return self.question_set.count()

    @property
    def actual_total_points(self):
        return self.points_per_question * self.actual_total_questions

    @property
    def total_points(self):
        return self.points_per_question * self.number_of_questions


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.TextField()

    def __str__(self):
        return self.question

    def get_correct_option(self):
        return Option.objects.get(question=self, is_correct=True)

    def get_option_count(self):
        return self.option_set.count()


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.option

    def get_correct_answer(self):
        return self.question.get_correct_option().option


class Score(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    answers = models.ManyToManyField(Option, related_name="answers")
    time_taken = models.DurationField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.score} - {self.quiz}"

    def get_total_points(self):
        return self.quiz.points_per_question * self.quiz.number_of_questions

    def get_percent_score(self):
        return f"{(self.score/self.get_total_points())*100:.2f} %"
