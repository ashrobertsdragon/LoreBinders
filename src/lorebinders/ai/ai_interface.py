from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from lorebinders.ai.ai_models._model_schema import (
    APIProvider,
    Model,
    ModelFamily,
)
from lorebinders.ai.ai_type import AIType
from lorebinders.ai.exceptions import MissingAIProviderError

if TYPE_CHECKING:
    from lorebinders._type_annotations import RateLimitManager


class AIModelConfig:
    """Configuration class for AI model settings."""

    def __init__(self, api_provider: APIProvider) -> None:
        """Initialize AI model configuration.

        Args:
            api_provider: The API provider configuration.
        """
        self.api_provider = api_provider
        self.provider = self.api_provider.api

    def initialize_api(self, rate_limiter: RateLimitManager) -> AIInterface:
        """Load the AI implementation based on the provider.

        Args:
            rate_limiter: Rate limiter for API calls.

        Returns:
            An instance of the AI implementation.

        Raises:
            MissingAIProviderError: If the provider is invalid.
        """
        try:
            module = importlib.import_module(
                f"api_{self.provider}", package="ai.ai_classes"
            )
            provider_class = f"{self.provider.capitalize()}API"
            implementation_class = getattr(module, provider_class)
            return AIInterface(implementation_class, rate_limiter)
        except (ImportError, AttributeError) as e:
            error_msg = f"Invalid AI provider: {self.provider}"
            logging.error(error_msg)
            raise MissingAIProviderError(error_msg) from e


class AIInterface:
    """Common interface to access all AI APIs.

    This class acts as a facade to different AI API implementations,
    providing a unified interface for AI operations.
    """

    def __init__(
        self, ai_implementation: AIType, rate_limiter: RateLimitManager
    ) -> None:
        """Initialize the AI interface.

        Args:
            ai_implementation: The AI implementation instance.
            rate_limiter: Rate limiter for API calls.
        """
        self._ai = ai_implementation
        self._rate_limiter = rate_limiter

    def set_family(self, model_config: AIModelConfig, family: str) -> None:
        """Set the model family for the AI implementation.

        Args:
            model_config: AI model configuration.
            family: Name of the model family to set.
        """
        self._family = model_config.api_provider.get_ai_family(family)

    def set_model(self, model_id: int) -> None:
        """Retrieve model from configuration and set it.

        Args:
            model_id: ID of the model to set.
        """
        model = self._family.get_model_by_id(model_id)
        self._ai.set_model(model, self._rate_limiter)
        self._model = model

    def get_model_by_id(self, model_id: int) -> Model:
        """Retrieve model from configuration by ID.

        Args:
            model_id: ID of the model to retrieve.

        Returns:
            The model object.
        """
        return self._family.get_model_by_id(model_id)

    @property
    def model(self) -> Model:
        """Return the Model object.

        Returns:
            The current model object.
        """
        return self._model

    @property
    def family(self) -> ModelFamily:
        """Return the ModelFamily object.

        Returns:
            The current model family object.
        """
        return self._family

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """Facade method that calls the AI provider's call_api method.

        Args:
            api_payload: Dictionary containing API parameters.
            json_response: Whether to expect JSON response format.
            retry_count: Current retry attempt count.
            assistant_message: Optional previous assistant message.

        Returns:
            The API response text.
        """
        return self._ai.call_api(
            api_payload, json_response, retry_count, assistant_message
        )

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Create a payload dictionary for making API calls.

        Args:
            prompt: The prompt text for the AI model.
            role_script: The role script text for the AI model.
            temperature: The temperature value for the AI model.
            max_tokens: The maximum number of tokens for the AI model.

        Returns:
            The payload dictionary containing model parameters.
        """
        return self._ai.create_payload(
            prompt, role_script, temperature, max_tokens
        )
