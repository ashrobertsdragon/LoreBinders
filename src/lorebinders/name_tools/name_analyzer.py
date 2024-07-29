from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._type_annotations import (
        AIInterface,
        Chapter,
    )
from lorebinders._types import InstructionType
from lorebinders.name_tools import name_tools
from lorebinders.role_script import RoleScript

BASE_CATEGORIES: list[str] = ["Characters", "Settings"]


@dataclass(slots=True, frozen=True)
class Instructions:
    """
    The instruction strings for the role scripts.
    """

    base: str
    character: str
    settings: str


@dataclass(slots=True, frozen=True)
class RoleScriptHelper:
    """
    The additional information needed to build the role scripts.
    """

    instruction_type: InstructionType
    absolute_max_tokens: int
    instructions: Instructions
    added_character_traits: list[str] | None


@lru_cache(maxsize=None)
def get_tokens_per(instruction_type: InstructionType) -> dict[str, int]:
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
        if instruction_type == InstructionType.MARKDOWN
        else json_tokens
    )


def generate_json_schema(
    category: str,
    added_traits: list[str] | None,
    default_traits: dict[str, list[str]],
) -> str:
    """
    Generates the JSON schema for the analysis.

    Args:
        category (str): The category to generate the schema for.
        added_traits (list[str] | None): The user added traits to include in

    Returns:
        str: The schema for the analysis.
    """

    traits: list[str] = default_traits.get(category, []) + (added_traits or [])
    schema_stub: dict[str, str] | str = (
        {trait: "Description" for trait in traits} if traits else "Description"
    )
    return json.dumps({category: schema_stub})


def generate_markdown_schema(
    category: str,
    added_traits: list[str] | None,
    default_traits: dict[str, list[str]],
) -> str:
    """
    Generates the Markdown schema for the analysis.

    Args:
        category (str): The category to generate the schema for.
        added_traits (list[str] | None): The user added traits to include in

    Returns:
        str: The schema for the analysis.
    """
    traits: list[str] = default_traits.get(category, []) + (added_traits or [])
    schema = f"# {category}\n"
    for trait in traits:
        schema += f"## {trait}\nDescription\n"
    return schema


def generate_schema(
    category: str,
    added_traits: list[str] | None,
    instruction_type: InstructionType,
) -> str:
    """
    Generates the schema for the analysis.

    Args:
        category (str): The category to generate the schema for.
        added_traits (list[str] | None): The user added traits to include in
        instruction_type (str): The format of the AI response.

    Returns:
        str: The schema for the analysis.
    """
    default_traits: dict[str, list[str]] = {
        "Characters": [
            "Appearance",
            "Personality",
            "Mood",
            "Relationships with other characters",
        ],
        "Settings": [
            "Appearance",
            "Relative location",
            "Familiarity for main character",
        ],
    }
    match instruction_type:
        case InstructionType.MARKDOWN:
            return generate_markdown_schema(
                category, added_traits, default_traits
            )
        case instruction_type.JSON:
            return generate_json_schema(category, added_traits, default_traits)
        case _:
            raise ValueError(
                f"Unsupported instruction type: {instruction_type}"
            )


def initialize_instructions(instruction_type: InstructionType) -> Instructions:
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
            instruction_type=instruction_type,
        ),
        character=name_tools.get_instruction_text(
            "character_instructions.txt", instruction_type=instruction_type
        ),
        settings=name_tools.get_instruction_text(
            "settings_instructions.txt", instruction_type=instruction_type
        ),
    )


def initialize_role_script_helper(
    instruction_type: InstructionType,
    absolute_max_tokens: int,
    instructions: Instructions,
    added_character_traits: list[str] | None = None,
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
        added_character_traits=added_character_traits,
    )


def initialize_helpers(
    instruction_type: InstructionType,
    absolute_max_tokens: int,
    added_character_traits: list[str] | None = None,
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
        instruction_type,
        absolute_max_tokens,
        instructions,
        added_character_traits,
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
    result = [instructions.base]

    if "Characters" in categories:
        result.append(instructions.character)
    if "Settings" in categories:
        result.append(instructions.settings)

    if other_categories := [
        cat for cat in categories if cat not in BASE_CATEGORIES
    ]:
        result.append(
            f"Provide descriptions of {', '.join(other_categories)}"
            " without referencing specific characters or plot points"
        )

    result.append(
        "You will format this information using the following schema where"
        ' "description" is replaced with the actual information.\n'
    )

    return "\n".join(result)


def create_role_script(
    categories: list[str],
    max_tokens: int,
    helper: RoleScriptHelper,
    instruction_type: InstructionType,
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
    instruction_text: str = create_instructions(
        categories, helper.instructions
    )
    schema_text: str = "".join(
        generate_schema(
            category, helper.added_character_traits, instruction_type
        )
        for category in categories
    )
    return RoleScript(instruction_text + schema_text, max_tokens)


def calculate_category_tokens(
    names: list[str],
    instruction_type: InstructionType,
    category: str,
    max_tokens: int,
) -> int:
    """
    Calculates the number of tokens for a category.

    Args:
        names (list[str]): The names to include in the batch.
        instruction_type (InstructionType): The format of the AI response.
        category (str): The category to include in the batch.
        max_tokens (int): The maximum number of tokens for the batch.

    Returns:
        int: The number of tokens for the category.
    """
    tokens_per: dict[str, int] = get_tokens_per(instruction_type)
    return min(
        len(names) * tokens_per.get(category, tokens_per["Other"]), max_tokens
    )


def should_create_new_role_script(
    current_tokens: int, category_tokens: int, max_tokens: int
) -> bool:
    """
    Checks if a new role script should be created.

    Args:
        current_tokens (int): The number of tokens in the current role script.
        category_tokens (int): The number of tokens for the current category.
        max_tokens (int): The maximum number of tokens for the role script.

    Returns:
        bool: True if a new role script should be created, False otherwise.
    """
    return current_tokens + category_tokens > max_tokens


def append_role_script(
    role_scripts: list[RoleScript],
    current_categories: list[str],
    current_tokens: int,
    helper: RoleScriptHelper,
    instruction_type: InstructionType,
) -> list[RoleScript]:
    """
    Appends a new role script to the list of role scripts.

    Args:
        role_scripts (list[RoleScript]): The list of role scripts.
        current_categories (list[str]): The categories in the current role
            script.
        current_tokens (int): The number of tokens in the current role script.
        instructions (Instructions): The instructions for the analysis.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        list[RoleScript]: The updated list of role scripts.
    """
    role_scripts.append(
        create_role_script(
            current_categories,
            current_tokens,
            helper,
            instruction_type,
        )
    )
    return role_scripts


def build_role_scripts(
    chapter_data: dict[str, list[str]],
    helper: RoleScriptHelper,
    instruction_type: InstructionType,
) -> list[RoleScript]:
    """
    Builds the role scripts for the AI.

    Args:
        chapter_data (dict[str, list[str]]): The data of the chapter.
        helper (RoleScriptHelper): A dataclass of additional arguments.
        instructions (Instructions): The instructions for the analysis.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        list[RoleScript]: The role scripts for the AI.
    """

    if not chapter_data:
        return []

    role_scripts: list[RoleScript] = []
    current_categories: list[str] = []
    current_tokens: int = 0

    for category, names in chapter_data.items():
        category_tokens: int = calculate_category_tokens(
            names,
            helper.instruction_type,
            category,
            helper.absolute_max_tokens,
        )

        if (
            should_create_new_role_script(
                current_tokens, category_tokens, helper.absolute_max_tokens
            )
            and current_categories
        ):
            role_scripts = append_role_script(
                role_scripts,
                current_categories,
                current_tokens,
                helper,
                instruction_type,
            )
            current_categories, current_tokens = [], 0

        current_categories.append(category)
        current_tokens += category_tokens

    if current_categories:
        role_scripts = append_role_script(
            role_scripts,
            current_categories,
            current_tokens,
            helper,
            instruction_type,
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


def parse_response(response: str, json_mode: bool) -> dict:
    """
    Parses the response from the AI model based on the instruction type to
    form a dictionary.

    Args:
        response (str): The response from the AI model.
        json_mode (bool): Whether the response is formatted as JSON or not.

    Returns:
        dict: A dictionary containing the names categorized by their respective
            categories.
    """
    if json_mode:
        from lorebinders.json_tools import RepairJSON

        return RepairJSON().json_str_to_dict(response)
    else:
        from lorebinders.markdown_parser import markdown_to_dict

        return markdown_to_dict(response)


def analyze_names(
    ai: AIInterface,
    instruction_type: InstructionType,
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
            ai=ai,
            role_script=script,
            prompt=f"Text: {chapter.text}",
            temperature=0.4,
            json_mode=json_mode,
        )
        for script in role_scripts
    ]
    combined_response: str = combine_responses(
        responses=responses, json_mode=json_mode
    )
    return parse_response(
        response=combined_response,
        json_mode=json_mode,
    )
