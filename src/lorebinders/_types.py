from __future__ import annotations

from logging import Logger
from typing import TYPE_CHECKING, Literal, TypeVar

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
    from lorebinders.ai.exceptions import (
        KeyNotFoundError,
        MaxRetryError,
        NoMessageError
    )
    from lorebinders.binders import Binder
    from lorebinders.book import Book, Chapter
    from lorebinders.book_dict import BookDict

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]

__all__ = [
    "FinishReason",
    "ChatCompletion",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionUserMessageParam",
    "ResponseFormat",
    "BookDict",
    "Book",
    "Chapter",
    "Binder",
    "Logger",
    "AIProviderManager",
    "EmailManager",
    "ErrorManager",
    "RateLimitManager",
    "T",
    "MaxRetryError",
    "NoMessageError",
    "KeyNotFoundError",
]
