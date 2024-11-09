import threading
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django_tables2 import SingleTableView
from content.models import BaseProcessModel
from documents.models import ContextFile
from documents.signals import process_files
from planning.signals import check_files_ready_signal
from services.models import get_default_request_config
from .forms import CreatePlanForm, DeletePlanForm, DeleteSessionForm
from .models import Plan, Session
from .tables import PlanTable, SessionTable
import os
import logging

logger = logging.getLogger("django.server")


# Create your views here.
def plan_details(request, plan_id):
    return render(request, "planning/plan_details.html", {"plan_id": plan_id})


def signal_files_ready(context_files, instance):
    process_files(context_files, instance.request_config.language_model.name)
    check_files_ready_signal(context_files, instance)


def add_to_context_files(context_file, instance: Plan):
    instance.materials_used.add(context_file)
    instance.save()


def process_uploaded_files(uploaded_files, instance: BaseProcessModel):
    new_context_files = []
    for file in uploaded_files:
        new_file = ContextFile(
            file=file, user=instance.user, filename=os.path.basename(file.name)
        )
        new_context_files.append(new_file)
    ContextFile.objects.bulk_create(new_context_files)
    instance.context_files.set(new_context_files)
    if not instance.request_config:
        instance.request_config = get_default_request_config()
        instance.save()
    thread = threading.Thread(
        target=signal_files_ready,
        args=(new_context_files, instance),
    )
    thread.start()


def process_selected_files(selected_files, instance: BaseProcessModel):
    instance.context_files.set(selected_files)
    thread = threading.Thread(
        target=check_files_ready_signal, args=(selected_files, instance)
    )
    thread.start()


def create_plan(request):
    if request.method == "POST":
        form = CreatePlanForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user
            uploaded_files = form.cleaned_data["files"]
            selected_files = form.cleaned_data["selected_files"]
            plan = form.save()
            if uploaded_files:
                process_uploaded_files(uploaded_files, plan)
            if selected_files:
                process_selected_files(selected_files, plan)

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def delete_plan(request, plan_id):
    if request.method == "POST":
        form = DeletePlanForm(request.POST)
        if form.is_valid():
            plan = Plan.objects.get(pk=plan_id)
            plan.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def plan_details(request, plan_id):
    plan = Plan.objects.get(pk=plan_id)
    return render(request, "planning/plan_details.html", {"plan": plan})


def toggle_marked_done(request):
    # if request.method == "POST":
    session = Session.objects.get(pk=request.GET.get("record_id"))
    session.marked_done = request.GET.get("marked_done") == "on"
    session.save()

    return redirect("plan_sessions", plan_id=session.plan.id)


class PlanListView(SingleTableView):
    model = Plan
    table_class = PlanTable
    template_name = "planning/plans.html"
    context_object_name = "plans"
    table_pagination = {"per_page": 10}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_form"] = CreatePlanForm()
        if context["plans"]:
            context["delete_forms"] = [
                DeletePlanForm(instance=plan) for plan in context["plans"]
            ]
        return context


def delete_session(request, session_id):
    if request.method == "POST":
        form = DeleteSessionForm(request.POST)
        if form.is_valid():
            session = Session.objects.get(pk=session_id)
            session.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class SessionListView(SingleTableView):
    model = Session
    table_class = SessionTable
    template_name = "planning/sessions.html"
    context_object_name = "sessions"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        return Session.objects.filter(plan=self.kwargs["plan_id"]).order_by("date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plan_goal"] = Plan.objects.get(pk=self.kwargs["plan_id"]).plan_goal
        if context["sessions"]:
            context["delete_forms"] = [
                DeleteSessionForm(instance=session) for session in context["sessions"]
            ]
        return context
