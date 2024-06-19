import importlib
import logging
from typing import Dict, Optional

from _model_schema import AIModels
from ai_factory import AIType
from exceptions import MissingAIProviderError


class AIModelConfig:
    def __init__(self, models: AIModels) -> None:
        self.provider_models = models
        self.provider = self.provider_models.provider
        self._cached_classes: Dict[str, AIType] = {}

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
            if self.provider not in self._cached_classes:
                module = importlib.import_module(
                    f"api_{self.provider}", package="ai_classes"
                )
                provider_class = f"{self.provider.capitalize()}API"
                implementation_class: AIType = getattr(module, provider_class)
                self._cached_classes[self.provider] = implementation_class()
            else:
                implementation_class = self._cached_classes[self.provider]
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

    def __init__(self, ai_implementation: AIType):
        self._ai = ai_implementation

    def set_model(self, model_config: AIModelConfig, model_id: int) -> None:
        """
        Retrieve model dictionary from configuration and pass it to
        implementation class.
        """
        model = model_config.provider_models.models.get_model_by_id(model_id)
        return self.ai_implementation.set_model(model)

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: Optional[str] = None,
    ) -> str:
        """
        Calls the 'call_api method of the actual AI API class.
        """
        return self.ai_implementation.call_api(
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
        return self.ai_implementation.create_payload(
            prompt, role_script, temperature, max_tokens
        )
