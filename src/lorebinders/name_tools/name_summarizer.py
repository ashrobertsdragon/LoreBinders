from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import AIInterface

from lorebinders.name_tools import name_tools
from lorebinders.prompt_generator import create_prompts
from lorebinders.role_script import RoleScript


def build_role_script() -> RoleScript:
    """
    Build the RoleScript
    """
    system_message = (
        "You are an expert summarizer. Please summarize the description "
        "over the course of the story for the following:"
    )
    return RoleScript(system_message, 200)  # max_tokens set to 200


def parse_response(
    response: str, lorebinder: dict, current_category: str, current_name: str
) -> dict:
    """
    Parses the response from the AI model to extract names and add them to the
    Chapter object.
    """
    if response and current_category and current_name:
        lorebinder[current_category][current_name] = {"summary": response}
    return lorebinder


def summarize_names(ai: AIInterface, lorebinder: dict) -> dict:
    """
    Summarize the names in the lorebinder.

    Args:
        ai (AIInterface): The AIInterface object.
        lorebinder (dict): The lorebinder to summarize.

    Returns:
        dict: The summarized lorebinder.
    """
    role_script: RoleScript = build_role_script()
    temperature: float = 0.4
    json_mode: bool = False

    for category, name, prompt in create_prompts(lorebinder):
        response = name_tools.get_ai_response(
            ai, role_script, prompt, temperature, json_mode
        )
        lorebinder = parse_response(response, lorebinder, category, name)

    return lorebinder
