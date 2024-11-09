from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from .models import ContextFile
from services.llm_handler import get_markdown
from chat.models import Message
import fitz
import pymupdf4llm
import tiktoken
import os
import logging
import json
from django.utils import timezone

logger = logging.getLogger("django.server")


@receiver(pre_delete, sender=ContextFile)
def delete_empty_messages(sender, instance, **kwargs):
    messages = Message.objects.filter(context_files=instance)

    for message in messages:
        message.context_files.remove(instance)

        if not message.context_files.exists():
            message.delete()


# add a queue for multiple files
def process_pdf(file_bytes, model_name):
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    markdown_json = pymupdf4llm.to_markdown(doc, page_chunks=True, show_progress=False)
    full_text = "".join([chunk["text"] for chunk in markdown_json])

    # Tokenize the extracted text
    encoder = tiktoken.encoding_for_model(model_name)
    tokenized_text = encoder.encode(full_text)

    return {
        "full_text": full_text,
        "markdown_json": markdown_json,
        "token_amount": len(tokenized_text),
    }


def process_txt(file_bytes, model_name):
    full_text = file_bytes.decode("utf-8")

    # Tokenize the extracted text
    encoder = tiktoken.encoding_for_model(model_name)
    tokenized_text = encoder.encode(full_text)

    return {
        "full_text": full_text,
        "markdown_json": None,  # No markdown for TXT
        "token_amount": len(tokenized_text),
    }


def process_context_file(context_file: ContextFile, model_name: str):
    file_path = context_file.file.path
    ext = os.path.splitext(file_path)[1].lower()
    file_bytes = context_file.file.read()
    if ext == ".pdf":
        data = process_pdf(file_bytes, model_name)
    elif ext == ".txt":
        data = process_txt(file_bytes, model_name)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    data["html"] = get_markdown(data["full_text"])
    return data


def handle_file_processing(context_file: ContextFile, model_name: str):
    """Function to handle file processing in a separate thread."""
    start_time = timezone.now()
    context_file.processing_status = "processing"
    context_file.save(update_fields=["processing_status"])
    try:
        processed_data = process_context_file(context_file, model_name)
    except Exception as e:
        logger.error(f"Error processing file {context_file.file.name}: {e}")
        context_file.processing_status = "error"
        raise e
    else:
        # Update the instance with processed data
        context_file.full_text = processed_data["full_text"]
        context_file.markdown_json = json.loads(
            json.dumps(processed_data["markdown_json"], ensure_ascii=False, default=str)
        )
        context_file.token_amount = processed_data["token_amount"]
        context_file.processing_status = "complete"
        context_file.html = processed_data["html"]
        context_file.processing_time = timezone.now() - start_time
    context_file.save()


def process_files(context_files, model_name: str):
    for context_file in context_files:
        if context_file.processing_status == "pending":
            handle_file_processing(context_file, model_name)


@receiver(post_delete, sender=ContextFile)
def delete_file_on_instance_delete(sender, instance, **kwargs):
    """
    Deletes the file from the file system when the corresponding
    `ContextFile` instance is deleted.
    """
    if instance.file:
        # Check if the file exists and delete it
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
