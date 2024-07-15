from __future__ import annotations

import os

import lorebinders.file_handling as file_handling
from lorebinders.ai.ai_interface import AIInterface
from lorebinders.role_script import RoleScript


class NameTools:
    """
    Mixin class for providing interface for AI to Name classes.
    """

    def __init__(self, ai: AIInterface) -> None:
        self._ai = ai
        self._categories_base: list[str] = ["Characters", "Settings"]
        self.temperature: float = 0.7
        self.json_mode: bool = False

    def _get_instruction_text(
        self, file_name: str, *, prompt_type: str | None = None
    ) -> str:
        if prompt_type is not None:
            os.path.join("instructions", prompt_type, file_name)
        else:
            file_path = os.path.join("instructions", file_name)
        return file_handling.read_text_file(file_path)

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
