from _typeshed import Incomplete
from ai_factory import AIFactory

from _types import (
    ChatCompletionAssistantMessageParam as ChatCompletionAssistantMessageParam,
)
from _types import (
    ChatCompletionSystemMessageParam as ChatCompletionSystemMessageParam,
)
from _types import (
    ChatCompletionUserMessageParam as ChatCompletionUserMessageParam,
)
from _types import ErrorManager as ErrorManager
from _types import FileManager as FileManager
from _types import ResponseFormat as ResponseFormat
from ai_classes import ChatCompletion as ChatCompletion
from ai_classes import FinishReason as FinishReason
from ai_classes import NoMessageError as NoMessageError

class OpenAIAPI(AIFactory):
    openai_client: Incomplete
    def __init__(
        self,
        file_manager: FileManager,
        error_manager: ErrorManager,
        model_key: str,
    ) -> None: ...
    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]: ...
    def call_api(
        self,
        api_payload: dict[str, str],
        retry_count: int = 0,
        json_response: bool = False,
        assistant_message: str | None = None,
    ) -> str: ...
    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]: ...
    def process_response(
        self,
        content_tuple: tuple[str, int, FinishReason],
        assistant_message: str | None,
        api_payload: dict,
        retry_count: int,
        json_response: bool,
    ) -> str: ...
