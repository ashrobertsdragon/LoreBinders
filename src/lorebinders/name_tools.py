from __future__ import annotations

from lorebinders._managers import RateLimitManager
from lorebinders.ai.ai_interface import AIModelConfig
from lorebinders.ai.ai_models._model_schema import APIProvider
from lorebinders.role_script import RoleScript


class NameTools:
    """
    Mixin class for providing interface for AI to Name classes.
    """

    def set_variables(self) -> None:
        self._categories_base: list[str] = ["Characters", "Settings"]
        self.temperature: float = 0.7
        self.json_mode: bool = False

    def initialize_api(
        self, provider: APIProvider, rate_limiter: RateLimitManager
    ) -> None:
        """
        Initialize the AI API with the provided schema.

        Args:
            provider (APIProvider): A dataclass of the AI API information.
            rate_limiter (RateLimitManager): An implementation of the
            abstract rate limiter.
        """

        self._ai_config = AIModelConfig(provider)
        self._ai = self._ai_config.initialize_api(rate_limiter)

    def set_family(self, family: str) -> None:
        """
        Set the model family for the AI implementation.
        """
        self._ai.set_family(family)

    def set_model(self, model_id: int) -> None:
        """
        Retrieve model dictionary from configuration and pass it to the AI.
        """
        self._ai.set_model(self._ai_config, model_id)

    def _get_ai_response(self, role_script: RoleScript, prompt: str) -> str:
        """
        Create the payload to send to the AI and send it.
        """
        payload = self._ai.create_payload(
            prompt,
            role_script.script,
            self.temperature,
            role_script.max_tokens,
        )
        return self._ai.call_api(payload, self.json_mode)
