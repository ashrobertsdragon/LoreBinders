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
    from ._managers import (
        AIProviderManager,
        EmailManager,
        ErrorManager,
        RateLimitManager
    )
    from .ai.exceptions import KeyNotFoundError, MaxRetryError, NoMessageError
    from .binders import Binder
    from .book import Book, Chapter
    from .book_dict import BookDict

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
