from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from lorebinders._managers import RateLimitManager
    from lorebinders._type_annotations import ChatCompletion, FinishReason
    from lorebinders.ai.ai_models._model_schema import Model


class AIType(Protocol):
    """Defines the interface for facade class AI interaction.

    This protocol defines the methods that all AI provider classes must
    implement.
    """

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Create API payload for the request.

        Args:
            prompt: The prompt text for the AI.
            role_script: The role/system message for the AI.
            temperature: The temperature setting for response randomness.
            max_tokens: Maximum tokens in the response.

        Returns:
            The formatted API payload dictionary.
        """
        ...

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """Call the AI API with the provided payload.

        Args:
            api_payload: The API request payload.
            json_response: Whether to request JSON response format.
            retry_count: Number of retries attempted.
            assistant_message: Optional assistant message for context.

        Returns:
            The API response content.
        """
        ...

    def modify_payload(self, api_payload: dict, **kwargs) -> dict:
        """Modify the API payload with additional parameters.

        Args:
            api_payload: The base API payload to modify.
            **kwargs: Additional parameters to include.

        Returns:
            The modified API payload.
        """
        ...

    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]:
        """Preprocess the raw API response.

        Args:
            response: The raw API response object.

        Returns:
            Tuple of (content, token_count, finish_reason).
        """
        ...

    def process_response(
        self,
        content_tuple: tuple[str, int, FinishReason],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        assistant_message: str | None = None,
    ) -> str:
        """Process the preprocessed response content.

        Args:
            content_tuple: Tuple of (content, token_count, finish_reason).
            api_payload: The original API payload.
            retry_count: Number of retries attempted.
            json_response: Whether JSON response was requested.
            assistant_message: Optional assistant message for context.

        Returns:
            The processed response content.
        """
        ...

    def set_model(self, model: Model, rate_handler: RateLimitManager) -> None:
        """Set the AI model and rate limit handler.

        Args:
            model: The AI model configuration to use.
            rate_handler: The rate limit manager for this model.
        """
        ...
