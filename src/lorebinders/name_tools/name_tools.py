from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._type_annotations import InstructionType
import lorebinders.file_handling as file_handling
from lorebinders.ai.ai_interface import AIInterface
from lorebinders.role_script import RoleScript


def get_instruction_text(
    file_name: str, *, instruction_type: InstructionType | None = None
) -> str:
    """
    Get the instruction text from the file.

    Args:
        file_name (str): The filename of the instruction text.
        prompt_type (str, optional): The type of prompt. Defaults to None.

    Returns:
        str: The instruction text read from the file.
    """

    prompt_type = instruction_type.value if instruction_type else ""
    file_path: str = os.path.join("instructions", prompt_type or "", file_name)
    return file_handling.read_text_file(file_path)


def get_ai_response(
    ai: AIInterface,
    role_script: RoleScript,
    prompt: str,
    temperature: float,
    json_mode: bool,
) -> str:
    """
    Create the payload to send to the AI and send it.

    Args:
        ai (AIInterface): The AI interface to use.
        role_script (RoleScript): The role script to use.
        prompt (str): The prompt to send to the AI.
        temperature (float): The temperature to use.
        json_mode (bool): Whether to use JSON mode or not.

    Returns:
        str: The response from the AI.
    """
    payload: dict = ai.create_payload(
        prompt,
        role_script.script,
        temperature,
        role_script.max_tokens,
    )
    return ai.call_api(payload, json_mode)
