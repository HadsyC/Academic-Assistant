import logging
from documents.models import ContextFile

logger = logging.getLogger("django.server")


def get_file_text(context_file_id: int) -> str:
    try:
        context_file = ContextFile.objects.get(id=context_file_id)
        logger.warning(f"File retrieved: {context_file.filename}")
        return context_file.get_full_text()
    except ContextFile.DoesNotExist:
        logger.error(f"File not found with id: {context_file_id}")
        return f"File not found with id {context_file_id}, perhaps it was deleted or never existed, are you sure the id is correct?"


CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_file_text",
            "description": "Get the full text of a given context file based on the context_file_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "context_file_id": {
                        "type": "integer",
                        "description": "The id of the context files to get the text from.",
                    },
                },
                "required": ["context_file_id"],
            },
        },
    }
]
