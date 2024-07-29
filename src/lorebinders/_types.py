from enum import Enum
from typing import Literal, TypeVar

T = TypeVar("T", dict, list, str)

FinishReason = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]


class InstructionType(Enum):
    MARKDOWN = "markdown"
    JSON = "json"
