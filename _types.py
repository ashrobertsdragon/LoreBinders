from logging import Logger
from typing import Literal, TypeVar

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.completion_create_params import ResponseFormat

from _managers import EmailManager, ErrorManager, FileManager
from ai_classes.ai_factory import AIFactory
from ai_classes.exceptions import (
    KeyNotFoundError,
    MaxRetryError,
    NoMessageError,
)
from binders import Binder
from book import Book, Chapter

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]

__all__ = [
    "AIFactory",
    "FinishReason",
    "ChatCompletion",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionUserMessageParam",
    "ResponseFormat",
    "Book",
    "Chapter",
    "Binder",
    "Logger",
    "EmailManager",
    "ErrorManager",
    "FileManager",
    "T",
    "MaxRetryError",
    "NoMessageError",
    "KeyNotFoundError",
]
