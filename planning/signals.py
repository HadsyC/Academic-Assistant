from datetime import datetime, timedelta
from django.dispatch import Signal, receiver
from documents.models import ContextFile, FileReference
from services.llm_handler import call_api, handle_tools_calls
from services.models import get_default_request_config
from .models import Plan, Session

plan_files_processed = Signal()


def create_session(
    plan_id, date, duration, session_goal, file_id, start_page_index, end_page_index
):

    date = datetime.strptime(date, "%Y-%m-%d")
    t = datetime.strptime(duration, "%H:%M:%S")
    duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    plan = Plan.objects.get(id=plan_id)
    file_ref = FileReference.objects.create(
        context_file=ContextFile.objects.get(id=file_id),
        start_page_index=start_page_index,
        end_page_index=end_page_index,
    )

    session = Session.objects.create(
        plan=plan,
        session_goal=session_goal,
        date=date,
        duration=duration,
    )
    session.file_references.add(file_ref)
    return session


def add_plan_details(plan_id: str, topic: str, description: str, explanation=None):
    plan = Plan.objects.get(id=plan_id)
    plan.topic = topic
    plan.description = description
    plan.explanation = explanation
    plan.save()


PLAN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_session",
            "description": "Create a single session for a given plan. Each session has a start and end date, and a goal. Make sure to provide the plan id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "The id of the plan to create the session for.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the session. The format is a string with the date in the format 'YYYY-MM-DD'.",
                    },
                    "duration": {
                        "type": "string",
                        "description": "The duration of the session. The format is a string with the duration in the format 'HH:MM:SS'.",
                    },
                    "session_goal": {
                        "type": "string",
                        "description": "A detailed description of what the goal of the session is. Don't mention the file but the concrete content of the session for study.",
                    },
                    "file_id": {
                        "type": "string",
                        "description": "The id of the file to reference in the session.",
                    },
                    "start_page_index": {
                        "type": "integer",
                        "description": "The page index to start the reference from.",
                    },
                    "end_page_index": {
                        "type": "integer",
                        "description": "The page index to end the reference to.",
                    },
                },
                "required": [
                    "plan_id",
                    "start",
                    "end",
                    "session_goal",
                    "file_id",
                    "start_page_index",
                    "end_page_index",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_plan_details",
            "description": "Add details to a plan. This function is used to add the topic, description, and explanation to a plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "The id of the plan to add details to.",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic of the plan.",
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the plan. Include some short summary of the plan and what it is about.",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "An optional explanation of why the different session occupy more or less the original plan time.",
                    },
                },
                "required": ["plan_id", "topic", "description"],
            },
        },
    },
]


def generate_sessions(messages, user, model):
    response = call_api(
        model=model, messages=messages, user=user, tools=PLAN_TOOLS, force_tool=True
    )
    tool_functions = {
        "create_session": create_session,
        "add_plan_details": add_plan_details,
    }
    for choice in response.choices:
        for i, tool_call in enumerate(choice.message.tool_calls):
            handle_tools_calls({i: tool_call.model_dump()}, tool_functions)


@receiver(plan_files_processed)
def create_plan_sessions(sender, **kwargs):
    context_files = kwargs.get("context_files")
    plan = kwargs.get("plan")
    full_text = "\n---\n".join(
        [
            f"File id: {context_file.id}\n{context_file.get_paginated_text()}"
            for context_file in context_files
        ]
    )
    prompt = f"""Create multiple study sessions for the following plan, a plan is a group of study sessions based on a multiple materials, each study session has a start date and time and end date and time, this can be the same day but different times. Make sure to provide the plan id:
    Plan ID: {plan.id}
    Plan Goal: {plan.plan_goal}
    Plan Start: {plan.start_date}
    Plan End: {plan.end_date}
    Materials for the study plan:

    {full_text}

    Remember, you are creating multiple sessions for this plan!"""
    if not plan.request_config:
        plan.request_config = get_default_request_config()
        plan.save()
    generate_sessions(
        [{"role": "system", "content": prompt}],
        plan.user,
        plan.request_config.language_model,
    )

    sessions = Session.objects.filter(plan=plan)
    session_goals = "\n".join([f"{session.session_goal}" for session in sessions])
    prompt = f"""The following sessions have been created for the plan (plan_id = {plan.id}):
    {session_goals}
    Now, add some details to the plan by calling the 'add_plan_details' function."""
    generate_sessions(
        [{"role": "system", "content": prompt}],
        plan.user,
        plan.request_config.language_model,
    )


def check_files_ready_signal(context_files, instance):
    while True:
        if all(
            [
                context_file.processing_status == "complete"
                for context_file in context_files
            ]
        ):
            break

    if context_files:
        kwargs = {
            "sender": Plan,
            "context_files": context_files,
            "plan": instance,
        }
        plan_files_processed.send(**kwargs)
