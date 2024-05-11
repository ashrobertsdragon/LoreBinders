from typing import Literal

from openai.types.chat.chat_completion import ChatCompletion

from book import Book, Chapter

FinishReason = Literal["stop", "length", "tool_calls", "content_filter", "function_call"]

__all__ = [FinishReason, ChatCompletion, Book, Chapter]