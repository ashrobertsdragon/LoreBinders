# name_extractor.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._type_annotations import Chapter

from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools import name_tools
from lorebinders.role_script import RoleScript
from lorebinders.sort_names import SortNames


def create_instructions() -> tuple[str, str]:
    """Creates the instructions for the name extractor.

    Returns:
        tuple[str, str]: A tuple containing the base instruction and the
            further instructions.
    """
    base_instruction: str = name_tools.get_instruction_text(
        "name_extractor_sys_prompt.txt"
    )
    further_instructions: str = name_tools.get_instruction_text(
        "name_extractor_instructions.txt"
    )
    return base_instruction, further_instructions


def build_custom_role(custom_categories: list[str] | None) -> str:
    """Creates a sample string to be added to the instructions.

    Based on a custom category list, creates sample instruction text.

    Args:
        custom_categories (list[str] | None): The user added categories to
            include in the instructions.

    Returns:
        str: The sample string to be added to the instructions.
    """
    if not custom_categories:
        return ""

    name_strings: list[str] = [
        f"{cat.strip()}:{cat.strip()}1, {cat.strip()}2, {cat.strip()}3"
        for cat in custom_categories
    ]
    return "\n".join(name_strings)


def build_role_script(
    custom_categories: list[str] | None, max_tokens: int = 1000
) -> RoleScript:
    """Builds the role script.

    Args:
        max_tokens (int): The maximum number of tokens for the AI to use.
        custom_categories (list[str] | None): The user added categories to
            include in the instructions.

    Returns:
        None
    """
    base_instructions, further_instructions = create_instructions()
    role_categories: str = build_custom_role(custom_categories)

    custom_category_str = (
        (", ".join(custom_categories) + "\n") if custom_categories else ""
    )

    system_message: str = (
        f"{base_instructions}\n{custom_category_str}"
        f"{further_instructions}\n{role_categories}"
    )
    return RoleScript(system_message, max_tokens=max_tokens)


def extract_names(
    ai: AIInterface,
    chapter: Chapter,
    role_script: RoleScript,
    narrator: str | None,
) -> dict:
    """Extracts names from the chapter text using the AI model.

    Args:
        ai (AIInterface): The AI interface to use.
        chapter (Chapter): The chapter to extract names from.
        role_script (RoleScript): The system message and max tokens to use.
        narrator (str | None): The narrator of the book if in third person.

    Returns:
        dict: A dictionary containing the names categorized by their respective
            categories.
    """
    temperature: float = 0.2
    json_mode: bool = False

    prompt = f"Text: {chapter.text}"

    response: str = name_tools.get_ai_response(
        ai, role_script, prompt, temperature, json_mode
    )
    return parse_response(response, narrator)


def parse_response(response: str, narrator: str | None) -> dict:
    """Parses the response from the AI model to extract names.

    Extracts names from the AI response and creates a dictionary.

    Args:
        response (str): The response from the AI model.
        narrator (str): The narrator of the book if in third person.

    Returns:
        dict: A dictionary containing the names categorized by their respective
            categories.
    """
    sorter = SortNames(response, narrator or "")
    return sorter.sort()
