import importlib
import logging
from typing import Dict, Optional

from _types import ErrorManager
from ai_classes.ai_factory import AIType


class AIInterface:
    """
    Load the AI implementation based on the provider. This class acts as a
    common interface to access all AI API's.

    Args:
        provider (str): The name of the AI provider.

    Returns:
        AIFactory: An instance of the AI implementation.

    Raises:
        ValueError: If the provider is invalid.
    """

    def __init__(
        self,
        provider: str,
        error_handler: ErrorManager,
        model_key: str,
    ) -> None:
        self.error_handler = error_handler
        self.model_key = model_key
        self._cached_classes: Dict[str, AIType] = {}

        self.ai_implementation: AIType = self._load_ai_implementation(provider)

    def _load_ai_implementation(self, provider: str) -> AIType:
        try:
            if provider not in self._cached_classes:
                module = importlib.import_module(
                    provider, package="ai_classes"
                )
                provider_class = f"{provider.capitalize()}API"
                implementation_class: AIType = getattr(module, provider_class)
                ai_class = implementation_class(
                    self.error_handler, self.model_key
                )
                self._cached_classes[provider] = ai_class
            else:
                ai_class = self._cached_classes[provider]
            return ai_class
        except (ImportError, AttributeError):
            logging.error(f"Invalid AI provider: {provider}")
            raise ValueError(f"Invalid AI provider: {provider}")

    def call_api(
        self,
        api_payload: dict,
        retry_count: Optional[int] = 0,
        assistant_message: Optional[str] = None,
    ) -> str:
        """
        Calls the 'call_api method of the actual AI API class.
        """
        return self.ai_implementation.call_api(
            api_payload, retry_count, assistant_message
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
        return self.ai_implementation.create_payload(
            prompt, role_script, temperature, max_tokens
        )
