from logging import Logger
from typing import Literal, TypeVar

from ai_classes.ai_factory import AIFactory
from openai.types.chat.chat_completion import ChatCompletion

from _managers import EmailManager, ErrorManager, FileManager
from book import Book, Chapter

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]

Completion = TypeVar("Completion", ChatCompletion)

__all__ = [
    "AIFactory",
    "FinishReason",
    "Completion",
    "Book",
    "Chapter",
    "Logger",
    "EmailManager",
    "ErrorManager",
    "FileManager",
    "T",
]
