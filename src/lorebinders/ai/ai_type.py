from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from lorebinders._managers import RateLimitManager
    from lorebinders._type_annotations import ChatCompletion, FinishReason
    from lorebinders.ai.ai_models._model_schema import Model


class AIType(Protocol):
    """
    Defines the interface used by the facade class to interact with the
    concrete AI classes.
    """

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict: ...

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str: ...

    def modify_payload(self, api_payload: dict, **kwargs) -> dict: ...

    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]: ...

    def process_response(
        self,
        content_tuple: tuple[str, int, FinishReason],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        assistant_message: str | None = None,
    ) -> str: ...

    def set_model(
        self, model: Model, rate_handler: RateLimitManager
    ) -> None: ...
