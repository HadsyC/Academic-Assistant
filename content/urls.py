from django.urls import path
from . import views

urlpatterns = [
    path("", views.base, name="content_base"),
    path("quizzes", views.QuizListView.as_view(), name="quizzes"),
    path("quizz_details/<str:quizz_id>/", views.quiz_details, name="quizz_details"),
    path("delete_quizz/<str:quizz_id>/", views.delete_quiz, name="delete_quizz"),
    path("create_quizz/", views.create_quiz, name="create_quizz"),
    path("score_details/<str:score_id>/", views.score_details, name="score_details"),
    path("summaries/", views.SummaryListView.as_view(), name="summaries"),
    path("create_summary/", views.create_summary, name="create_summary"),
    path(
        "delete_summary/<str:summary_id>/", views.delete_summary, name="delete_summary"
    ),
    path(
        "summary_details/<str:summary_id>/",
        views.summary_details,
        name="summary_details",
    ),
]
