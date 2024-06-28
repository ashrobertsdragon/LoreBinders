from __future__ import annotations

from abc import ABC, abstractmethod

from .ai.ai_interface import AIModelConfig
from .ai.ai_models._model_schema import APIProvider
from .role_script import RoleScript


class NameTools(ABC):
    """
    Abstract class for name classes
    """

    def initialize_api(self, ai_models: APIProvider) -> None:
        """
        Initialize the NameTools class an ModelFamily dataclass object.

        Args:
            ai_models (ModelFamily): A dataclass of the AI API information.
        """

        self._ai_config = AIModelConfig(ai_models)
        self._ai = self._ai_config.initialize_api()

        self._categories_base: list[str] = ["Characters", "Settings"]
        self.temperature: float = 0.7
        self._json_mode: bool = False

    def _get_ai_response(
        self, role_script: RoleScript, prompt, model_id: int
    ) -> str:
        """
        Create the payload to send to the AI and send it.
        """
        self._ai.set_model(self._ai_config, model_id)
        payload = self._ai.create_payload(
            prompt, role_script.script, role_script.max_tokens
        )
        return self._ai.call_api(payload, self._json_mode)

    @abstractmethod
    def _parse_response(self, response: str) -> dict:
        """
        Abstract method to parse the AI response.

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError(
            "Method _parse_response must be implemented in child class."
        )

    @abstractmethod
    def build_role_script(self) -> None:
        """
        Abstract method to build the role script

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError(
            "Method _build_role_script must be implemented in child class."
        )
