from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, TypeVar

from loguru import logger
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from openai.types.chat.completion_create_params import ResponseFormat

if TYPE_CHECKING:
    from lorebinders._managers import (
        AIProviderManager,
        EmailManager,
        ErrorManager,
        RateLimitManager
    )
    from lorebinders.ai.ai_interface import AIInterface
    from lorebinders.ai.exceptions import (
        KeyNotFoundError,
        MaxRetryError,
        NoMessageError
    )
    from lorebinders.book import Book, Chapter
    from lorebinders.book_dict import BookDict

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]


class InstructionType(Enum):
    MARKDOWN = "markdown"
    JSON = "json"


__all__ = [
    "FinishReason",
    "InstructionType",
    "ChatCompletion",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionUserMessageParam",
    "AIInterface",
    "ResponseFormat",
    "BookDict",
    "Book",
    "Chapter",
    "logger",
    "AIProviderManager",
    "EmailManager",
    "ErrorManager",
    "RateLimitManager",
    "T",
    "MaxRetryError",
    "NoMessageError",
    "KeyNotFoundError",
]
