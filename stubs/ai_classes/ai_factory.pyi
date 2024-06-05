import abc
from abc import ABC, abstractmethod

from _typeshed import Incomplete

from _types import ChatCompletion as ChatCompletion
from _types import ErrorManager as ErrorManager
from _types import FileManager as FileManager
from _types import FinishReason as FinishReason

class RateLimit:
    def __init__(self, model_key: str, file_handler: FileManager) -> None: ...
    def get_rate_limit_minute(self) -> float: ...
    def get_rate_limit_tokens_used(self) -> int: ...
    model_name: Incomplete
    context_window: Incomplete
    tokenizer: Incomplete
    def model_details(self) -> None: ...
    def get_model_details(self, model_key: str) -> dict: ...
    def is_rate_limit(self, model_key: str) -> int: ...

class AIFactory(ABC, RateLimit, metaclass=abc.ABCMeta):
    unresolvable_error_handler: Incomplete
    def __init__(
        self,
        file_manager: FileManager,
        error_manager: ErrorManager,
        model_key: str,
    ) -> None: ...
    def count_tokens(self, text: str) -> int: ...
    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict: ...
    def update_rate_limit_data(self, tokens: int) -> None: ...
    @abstractmethod
    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]: ...
    def modify_payload(self, api_payload: dict, **kwargs) -> dict: ...
    def error_handle(self, e: Exception, retry_count: int) -> int: ...
    def handle_rate_limiting(
        self, input_tokens: int, max_tokens: int
    ) -> None: ...
    @abstractmethod
    def call_api(
        self,
        api_payload: dict,
        retry_count: int | None = 0,
        assistant_message: str | None = None,
    ) -> str: ...
    @abstractmethod
    def process_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]: ...
