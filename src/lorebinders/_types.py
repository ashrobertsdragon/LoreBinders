from logging import Logger
from typing import Literal, TypeVar

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from openai.types.chat.completion_create_params import ResponseFormat

from _managers import EmailManager, ErrorManager
from ai_classes._model_schema import AIModels, Model
from ai_classes.ai_factory import AIType
from ai_classes.exceptions import (
    KeyNotFoundError,
    MaxRetryError,
    NoMessageError
)
from attributes import NameTools
from binders import Binder
from book import Book, Chapter
from book_dict import BookDict

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]

__all__ = [
    "AIType",
    "FinishReason",
    "ChatCompletion",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionUserMessageParam",
    "ResponseFormat",
    "BookDict",
    "Book",
    "Chapter",
    "NameTools",
    "Binder",
    "Logger",
    "AIModels",
    "Model",
    "EmailManager",
    "ErrorManager",
    "T",
    "MaxRetryError",
    "NoMessageError",
    "KeyNotFoundError",
]
