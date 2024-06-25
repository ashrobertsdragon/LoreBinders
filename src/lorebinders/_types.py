from logging import Logger
from typing import Literal, TypeVar

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from openai.types.chat.completion_create_params import ResponseFormat

from _managers import AIProviderManager, EmailManager, ErrorManager
from ai.ai_factory import AIType
from ai.ai_models._model_schema import (
    AIModelRegistry,
    APIProvider,
    Model,
    ModelFamily
)
from ai.exceptions import KeyNotFoundError, MaxRetryError, NoMessageError
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
    "AIModelRegistry",
    "APIProvider",
    "ModelFamily",
    "Model",
    "AIProviderManager",
    "EmailManager",
    "ErrorManager",
    "T",
    "MaxRetryError",
    "NoMessageError",
    "KeyNotFoundError",
]
