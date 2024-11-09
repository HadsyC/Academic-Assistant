from django.dispatch import Signal, receiver
from services.llm_handler import call_api, get_markdown, handle_tools_calls
from services.models import LanguageModel, get_default_request_config
from django.contrib.auth.models import User
import logging
import time
from .models import Quiz, Question, Option, Summary

logger = logging.getLogger("django.server")
quiz_files_processed = Signal()
summary_files_processed = Signal()


def create_question(
    quizz_id, question_text, options, correct_option_index, explanations
):
    quiz = Quiz.objects.get(id=quizz_id)
    logger.warning(f"Creating question for Quiz: {quiz.topic} ({quiz.id})")

    # Create the question
    question = Question.objects.create(quiz=quiz, question=question_text)
    logger.warning(f"Question: {question_text}")

    # Iterate through options and explanations together

    for i, (option, explanation) in enumerate(zip(options, explanations)):
        is_correct = i == correct_option_index  # Check if the current option is correct

        # Create the option with the associated explanation
        Option.objects.create(
            question=question,
            option=option,
            is_correct=is_correct,
            explanation=explanation,
        )


QUIZZ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_question",
            "description": "Create a single question for a given quizz. Each question has a text, options, correct option index, and explanations for each option. The amount of options must be equal to the amount of explanations and there must be a correct option index. Make sure to provide the quiz id and to add the correct amount of options and explanations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quizz_id": {
                        "type": "string",
                        "description": "The id of the quiz to create the question for.",
                    },
                    "question_text": {
                        "type": "string",
                        "description": "The text of the question to create.",
                    },
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "The options for the question. One of them must be the correct option.",
                    },
                    "correct_option_index": {
                        "type": "integer",
                        "description": "The index of the correct option in the options array.",
                    },
                    "explanations": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "The explanations for each option. The amount of explanations must be equal to the amount of options.",
                    },
                },
                "required": [
                    "quizz_id",
                    "question_text",
                    "options",
                    "correct_option_index",
                    "explanations",
                ],
            },
        },
    }
]


def generate_quizz_content(messages: list[dict], user: User, model: LanguageModel):
    response = call_api(
        model=model,
        messages=messages,
        user=user,
        tools=QUIZZ_TOOLS,
        force_tool=True,
    )
    tool_functions = {"create_question": create_question}
    for choice in response.choices:
        for i, tool_call in enumerate(choice.message.tool_calls):
            handle_tools_calls({i: tool_call.model_dump()}, tool_functions)


def check_question_number(
    quiz, actual_questions_generated, num_questions_asked, full_text
):
    already_generated_questions = [
        q for q in actual_questions_generated.values_list("question", flat=True)
    ]
    if actual_questions_generated.count() < num_questions_asked:
        logger.error(
            f"Failed to generate all questions for Quiz: {quiz.topic} ({quiz.id}) ({actual_questions_generated.count()} from {num_questions_asked})."
        )
        logger.error(f"Already generated questions: {already_generated_questions}")
        remaining_questions = num_questions_asked - actual_questions_generated.count()
        prompt = f"""You generated {actual_questions_generated.count()} questions from the {num_questions_asked} you requested. 
        
        Please try again and generate the remaining questions ({remaining_questions})! 
        You already generated the following questions:
        {already_generated_questions}
        
        quizz_id: {quiz.id}
        Difficulty: "{quiz.difficulty}"
        Number of questions: {quiz.number_of_questions}
        Options per question: {quiz.options_per_question}
        Points (score) per question: {quiz.points_per_question}
        Full context for the quizz:
    {full_text}"""
        messages = [{"role": "system", "content": prompt}]

        num_questions_asked = quiz.number_of_questions
        actual_questions_generated = Question.objects.filter(quiz=quiz)
        generate_quizz_content(messages, quiz.user, quiz.request_config.language_model)
        check_question_number(
            quiz,
            Question.objects.filter(quiz=quiz),
            quiz.number_of_questions,
            full_text,
        )
    else:
        logger.info(
            f"All questions were successfully generated for Quiz: {quiz.topic} ({quiz.id}) ({actual_questions_generated.count()} from {num_questions_asked})."
        )
        quiz.processing_status = "complete"
        quiz.save()


@receiver(quiz_files_processed)
def create_quiz(sender, **kwargs):
    context_files = kwargs.get("context_files")
    quiz = kwargs.get("instance")
    full_text = "\n---\n".join(
        [
            f"{context_file.filename}:\n{context_file.full_text}"
            for context_file in context_files
        ]
    )
    prompt = f"""Create a quiz with the following parameters!
    quizz_id: {quiz.id}
    Difficulty: "{quiz.difficulty}"
    Number of questions: {quiz.number_of_questions}
    Options per question: {quiz.options_per_question}
    Points (score) per question: {quiz.points_per_question}
    Full context for the quizz:
{full_text}"""

    messages = [{"role": "system", "content": prompt}]
    if not quiz.request_config:
        quiz.request_config = get_default_request_config()
        quiz.save()
    generate_quizz_content(messages, quiz.user, quiz.request_config.language_model)

    check_question_number(
        quiz, Question.objects.filter(quiz=quiz), quiz.number_of_questions, full_text
    )


def update_summary(summary_id, summary_text, topic):
    summary = Summary.objects.get(id=summary_id)
    summary.text = summary_text
    summary.topic = topic
    summary.html = get_markdown(
        ".. toc::\n\n---\n\n" + summary_text
    )  # add table of contents and line break
    summary.processing_status = "complete"
    summary.save()
    logger.info(f"Summary: {summary.topic} ({summary.id}) was successfully updated.")


SUMMARY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_summary",
            "description": "Update the text and topic of a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary_id": {
                        "type": "string",
                        "description": "The id of the summary to update.",
                    },
                    "summary_text": {
                        "type": "string",
                        "description": "The summary in markdown format. Text only! (in markdown)",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The new topic of the summary",
                    },
                },
                "required": ["summary_id", "summary_text", "topic"],
            },
        },
    }
]


def generate_summary_content(messages: list[dict], summary):
    user = summary.user
    if not summary.request_config:
        summary.request_config = get_default_request_config()
        summary.save()
    model = summary.request_config.language_model

    response = call_api(
        model=model,
        messages=messages,
        user=user,
        tools=SUMMARY_TOOLS,
        force_tool=True,
    )
    tool_functions = {"update_summary": update_summary}
    for choice in response.choices:
        for i, tool_call in enumerate(choice.message.tool_calls):
            handle_tools_calls({i: tool_call.model_dump()}, tool_functions)


@receiver(summary_files_processed)
def create_summary(sender, **kwargs):
    context_files = kwargs.get("context_files")
    summary = kwargs.get("instance")
    full_text = "\n---\n".join(
        [
            f"{context_file.filename}:\n{context_file.full_text}"
            for context_file in context_files
        ]
    )
    prompt = f"""Create a summary with the following parameters, the summary should contain all parts of the given context, if you ommited any part, please add a reason. The summary should be in markdown format and for any important statement you add the corresponding reference if provided.
    Take inspiration from Wikipedia articles. Be sure to use the correct tool to update the following summary!
    summary_id: {summary.id}
    Full context for the summary:
    {full_text}

    The summary should be concise and cover all the important parts of the context, it should be in markdown format and also respect the markdown hierarchy for titles and enumeration. Write in english! If the document includes definitions, copy the definitions exactly as they are in the document."""

    messages = [{"role": "system", "content": prompt}]
    generate_summary_content(messages, summary)


def check_files_ready_signal(context_files, instance):
    while True:
        # sleep 5 seconds
        time.sleep(5)
        if all(
            [
                context_file.processing_status == "complete"
                for context_file in context_files
            ]
        ):
            break

    if context_files:
        if isinstance(instance, Quiz):
            sender = Quiz
            signal = quiz_files_processed
        elif isinstance(instance, Summary):
            sender = Summary
            signal = summary_files_processed

        kwargs = {
            "sender": sender,
            "context_files": context_files,
            "instance": instance,
        }
        signal.send(**kwargs)
