from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from .ai_models._model_schema import APIProvider
from .ai_type import AIType
from .exceptions import MissingAIProviderError

if TYPE_CHECKING:
    from lorebinders._types import RateLimitManager


class AIModelConfig:
    def __init__(self, models: APIProvider) -> None:
        self.provider_models = models
        self.provider = self.provider_models.api

    def initialize_api(self):
        """
        Load the AI implementation based on the provider.

        Args:
            provider (str): The name of the AI provider.

        Returns:
            AIType: An instance of the AI implementation.

        Raises:
            ValueError: If the provider is invalid.
        """
        try:
            module = importlib.import_module(
                f"api_{self.provider}", package="ai.ai_classes"
            )
            provider_class = f"{self.provider.capitalize()}API"
            implementation_class = getattr(module, provider_class)
            return AIInterface(implementation_class)
        except (ImportError, AttributeError) as e:
            error_msg = f"Invalid AI provider: {self.provider}"
            logging.error(error_msg)
            raise MissingAIProviderError(error_msg) from e


class AIInterface:
    """
    Load the AI implementation based on the provider. This class acts as a
    common interface to access all AI API's.

    Args:
        provider (str): The name of the AI provider.

    Returns:
        AIType: An instance of the AI implementation.

    Raises:
        ValueError: If the provider is invalid.
    """

    def __init__(
        self, ai_implementation: AIType, rate_limiter: RateLimitManager
    ) -> None:
        self._ai = ai_implementation
        self._rate_limiter = rate_limiter

    def set_family(self, model_config: AIModelConfig, family: str) -> None:
        """
        Set the model family for the AI implementation.
        """
        self._family = model_config.provider_models.get_ai_family(family)

    def set_model(self, model_id: int) -> None:
        """
        Retrieve model dictionary from configuration and pass it to
        implementation class.
        """
        model = self._family.get_model_by_id(model_id)
        return self._ai.set_model(model, self._rate_limiter)

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """
        Calls the 'call_api method of the actual AI API class.
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
        """
        Calls the 'create_payload' method of the actual AI class which has:

        Creates a payload dictionary for making API calls to the AI engine.

        Args:
            prompt (str): The prompt text for the AI model.
            role_script (str): The role script text for the AI model.
            temperature (float): The temperature value for the AI model.
            max_tokens (int): The maximum number of tokens for the AI model.

        Returns:
            dict: The payload dictionary containing the following keys:
                    model_name (str): The name of the model.
                    role_script (str): The role script text.
                    prompt (str): The prompt text.
                    temperature (float): The temperature value.
                    max_tokens (int): The maximum number of tokens.

        Raises:
            ValueError: If the prompt input is not a string.
            ValueError: If the role_script input is not a string.
            ValueError: If the temperature input is not a float.
            ValueError: If the max_tokens input is not an integer.
            ValueError: If the model name is not set.

        """
        return self._ai.create_payload(
            prompt, role_script, temperature, max_tokens
        )
