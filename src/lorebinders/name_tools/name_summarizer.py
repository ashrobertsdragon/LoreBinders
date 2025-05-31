from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._type_annotations import AIInterface

from lorebinders import prompt_generator
from lorebinders.name_tools import name_tools
from lorebinders.role_script import RoleScript


def build_role_script(max_tokens: int = 200) -> RoleScript:
    """Builds the RoleScript.

    Args:
        max_tokens: Maximum number of tokens for the response.

    Returns:
        RoleScript: The configured role script for summarization.
    """
    system_message = (
        "You are an expert summarizer. Please summarize the description "
        "over the course of the story for the following:"
    )
    return RoleScript(system_message, max_tokens)


def update_lorebinder(
    response: str, lorebinder: dict, category: str, name: str
) -> dict:
    """Adds the response as a value to a new summary key.

    Adds to the appropriate section of the Lorebinder dictionary.

    Args:
        response (str): The response from the AI.
        lorebinder (dict): The lorebinder dictionary.
        category (str): The category the name is in.
        name (str): The name the summary is for.

    Returns:
        dict: The updated lorebinder dictionary.
    """
    if response and category and name:
        lorebinder[category][name] |= {"Summary": response}
    return lorebinder


def summarize_names(ai: AIInterface, lorebinder: dict) -> dict:
    """Summarize the names in the lorebinder.

    Args:
        ai (AIInterface): The AIInterface object.
        lorebinder (dict): The lorebinder to summarize.

    Returns:
        dict: The summarized lorebinder.
    """
    role_script: RoleScript = build_role_script()
    temperature: float = 0.4
    json_mode: bool = False

    for category, name, prompt in prompt_generator.create_prompts(lorebinder):
        response = name_tools.get_ai_response(
            ai, role_script, prompt, temperature, json_mode
        )
        lorebinder = update_lorebinder(response, lorebinder, category, name)

    return lorebinder
