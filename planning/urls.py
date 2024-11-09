from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.PlanListView.as_view(), name="plans"),
    path("create_plan/", views.create_plan, name="create_plan"),
    path("delete_plan/<str:plan_id>/", views.delete_plan, name="delete_plan"),
    path(
        "plan_sessions/<str:plan_id>",
        views.SessionListView.as_view(),
        name="plan_sessions",
    ),
    path(
        "delete_session/<int:session_id>/", views.delete_session, name="delete_session"
    ),
    path("toggle_marked_done/", views.toggle_marked_done, name="toggle_marked_done"),
]
