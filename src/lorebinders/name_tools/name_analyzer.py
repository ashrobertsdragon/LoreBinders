# name_analyzer.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import AIInterface, Chapter

from lorebinders.name_tools import name_tools
from lorebinders.role_script import RoleScript

BASE_CATEGORIES: list[str] = ["Characters", "Settings"]


@dataclass(frozen=True)
class Instructions:
    """
    The instruction strings for the role scripts.
    """

    base: str
    character: str
    settings: str


@dataclass(frozen=True)
class RoleScriptHelper:
    """
    The additional information needed to build the role scripts.
    """

    instruction_type: str
    absolute_max_tokens: int
    instructions: Instructions


def get_tokens_per(instruction_type: str) -> dict[str, int]:
    """
    Gets the tokens per for the analysis.

    Args:
        instruction_type (str): The format the AI is told to respond in.

    Returns:
        dict[str, int]: The tokens per for the analysis.
    """
    json_tokens: dict[str, int] = {
        "Characters": 200,
        "Settings": 150,
        "Other": 100,
    }
    return (
        {k: int(v * 0.85) for k, v in json_tokens.items()}
        if instruction_type == "markdown"
        else json_tokens
    )


def generate_schema(
    category: str,
    added_traits: list[str] | None,
) -> str:
    """
    Generates the schema for the analysis.

    Args:
        category (str): The category to generate the schema for.
        added_traits (list[str] | None): The user added traits to include in

    Returns:
        str: The schema for the analysis.
    """
    character_traits: list[str] = [
        "Appearance",
        "Personality",
        "Mood",
        "Relationships with other characters",
    ] + (added_traits or [])

    cat_attr_map: dict[str, list[str]] = {
        "Characters": character_traits,
        "Settings": [
            "Appearance",
            "Relative location",
            "Familiarity for main character",
        ],
    }

    schema_stub = (
        {attr: "Description" for attr in cat_attr_map[category]}
        if category in BASE_CATEGORIES
        else "Description"
    )
    return json.dumps({category: schema_stub})


def initialize_instructions(instruction_type: str) -> Instructions:
    """
    Initializes the instructions dataclass for the analysis.

    Args:
        instruction_type (str): The format to tell the AI to respond in.

    Returns:
        Instructions: The instructions for the analysis.
    """
    return Instructions(
        base=name_tools.get_instruction_text(
            "name_analyzer_base_instructions.txt",
            prompt_type=instruction_type,
        ),
        character=name_tools.get_instruction_text(
            "character_instructions.txt", prompt_type=instruction_type
        ),
        settings=name_tools.get_instruction_text(
            "settings_instructions.txt", prompt_type=instruction_type
        ),
    )


def initialize_role_script_helper(
    instruction_type: str, absolute_max_tokens: int, instructions: Instructions
) -> RoleScriptHelper:
    """
    Creates a dataclass of information needed to build the RoleScript objects.

    Args:
        instruction_type (str): The format the AI is told to respond in.

    Returns:
        RoleScriptHelper: The helper dataclass object.
    """
    return RoleScriptHelper(
        instruction_type=instruction_type,
        absolute_max_tokens=absolute_max_tokens,
        instructions=instructions,
    )


def initialize_helpers(
    instruction_type: str, absolute_max_tokens: int
) -> RoleScriptHelper:
    """
    Initializes the helpers for the analysis.

    Args:
        instruction_type (str): The format to tell the AI to respond in.
        absolute_max_tokens (int): The maximum number of tokens the AI model
            can respond with.

    Returns:
        RoleScriptHelper: The helper dataclass object.
    """
    instructions: Instructions = initialize_instructions(instruction_type)
    return initialize_role_script_helper(
        instruction_type, absolute_max_tokens, instructions
    )


def create_instructions(
    categories: list[str],
    instructions: Instructions,
) -> str:
    """
    Creates the instructions for the analysis.

    Args:
        categories (list[str]): The categories to include in the analysis.
        instructions (Instructions): The instructions for the analysis.


    Returns:
        str: The instructions for the analysis.
    """
    result: str = instructions.base

    if "Characters" in categories:
        result += f"\n{instructions.character}"
    if "Settings" in categories:
        result += f"\n{instructions.settings}"

    if other_categories := [
        cat for cat in categories if cat not in BASE_CATEGORIES
    ]:
        result += f"\nProvide descriptions of {', '.join(other_categories)}"
        result += " without referencing specific characters or plot points"

    return (
        result
        + "\nYou will format this information using the following schema where"
        + ' "description" is replaced with the actual information.\n'
    )


def create_role_script(
    categories: list[str],
    max_tokens: int,
    instructions: Instructions,
    added_character_traits: list[str] | None,
) -> RoleScript:
    """
    Creates the role script for the AI.

    Args:
        categories (list[str]): The categories to include in the analysis.
        max_tokens (int): The maximum number of tokens for the analysis.
        instructions (Instructions): The unchanging segments of the system
            instructions.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        RoleScript: The role script for the AI.
    """
    instruction_text: str = create_instructions(categories, instructions)
    schema_text: str = "".join(
        generate_schema(category, added_character_traits)
        for category in categories
    )
    return RoleScript(instruction_text + schema_text, max_tokens)


def build_role_scripts(
    chapter_data: dict,
    helper: RoleScriptHelper,
    added_character_traits: list[str] | None,
) -> list[RoleScript]:
    """
    Builds the role scripts for the AI.

    Args:
        chapter_data (dict): The data of the chapter.
        helper (RoleScriptHelper): A dataclass of additional arguments.
        instructions (Instructions): The instructions for the analysis.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        list[RoleScript]: The role scripts for the AI.
    """
    tokens_per: dict[str, int] = get_tokens_per(helper.instruction_type)
    role_scripts: list[RoleScript] = []
    categories: list = []
    current_tokens: int = 0

    for category, names in chapter_data.items():
        category_tokens: int = min(
            len(names) * tokens_per.get(category, tokens_per["Other"]),
            helper.absolute_max_tokens,
        )

        if (
            current_tokens + category_tokens > helper.absolute_max_tokens
            and categories
        ):
            role_scripts.append(
                create_role_script(
                    categories,
                    current_tokens,
                    helper.instructions,
                    added_character_traits,
                )
            )
            categories, current_tokens = [], 0

        categories.append(category)
        current_tokens += category_tokens

    if categories:
        role_scripts.append(
            create_role_script(
                categories,
                current_tokens,
                helper.instructions,
                added_character_traits,
            )
        )

    return role_scripts


def combine_responses(responses: list[str], json_mode: bool) -> str:
    """
    Combines the responses from the AI into a single string.

    Args:
        responses (list[str]): The responses from the AI.
        json_mode (bool): Whether to use JSON mode or not.

    Returns:
        str: The combined responses.
    """
    return (
        "{" + ",".join(part.strip("{}") for part in responses) + "}"
        if json_mode
        else "\n".join(responses)
    )


def parse_response(response: str, instruction_type: str) -> dict:
    """
    Parses the response from the AI model based on the instruction type to
    form a dictionary.

    Args:
        response (str): The response from the AI model.
        instruction_type (str): The format the AI was told to respond in.

    Returns:
        dict: A dictionary containing the names categorized by their respective
            categories.
    """
    if instruction_type == "json":
        from lorebinders.json_tools import RepairJSON

        return RepairJSON().json_str_to_dict(response)
    else:
        from lorebinders.markdown_parser import markdown_to_dict

        return markdown_to_dict(response)


def analyze_names(
    ai: AIInterface,
    instruction_type: str,
    role_scripts: list[RoleScript],
    chapter: Chapter,
) -> dict:
    """
    Analyzes the names in the chapter and returns the analysis.

    Args:
        ai (AIInterface): The AIInterface object.
        instruction_type (str): The format to tell the AI to respond in.
        role_scripts (list[RoleScript]): List of instructions and max tokens
            for the AI.
        chapter (Chapter): The chapter to analyze.

    Returns:
        dict: The analysis of the names.
    """

    json_mode = instruction_type == "json"
    responses: list[str] = [
        name_tools.get_ai_response(
            ai,
            script,
            f"Text: {chapter.text}",
            0.4,
            json_mode,
        )
        for script in role_scripts
    ]
    combined_response: str = combine_responses(
        responses=responses, json_mode=json_mode
    )
    return parse_response(
        response=combined_response,
        instruction_type=instruction_type,
    )
