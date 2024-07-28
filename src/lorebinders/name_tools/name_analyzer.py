# name_analyzer.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import BookDict, Chapter

from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools import name_tools
from lorebinders.role_script import RoleScript


@dataclass
class AnalyzerConfig:
    """
    The configuration for the name analysis
    """

    instruction_type: str
    absolute_max_tokens: int
    base_categories: list[str] = ["Characters", "Settings"]


@dataclass
class Instructions:
    """
    The instruction strings for the role scripts
    """

    base: str
    character: str
    settings: str


def get_tokens_per(instruction_type: str) -> dict[str, int]:
    """
    Gets the tokens per for the analysis.

    Args:
        instruction_type (str): The type of instruction to use.

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
    base_categories: list[str],
) -> str:
    """
    Generates the schema for the analysis.

    Args:
        category (str): The category to generate the schema for.
        added_traits (list[str] | None): The user added traits to include in
            the analysis.
        base_categories (list[str]): The base categories to include in the
            analysis.

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
        if category in base_categories
        else "Description"
    )
    return json.dumps({category: schema_stub})


def create_instructions(
    categories: list[str],
    instructions: Instructions,
    base_categories: list[str],
) -> str:
    """
    Creates the instructions for the analysis.

    Args:
        categories (list[str]): The categories to include in the analysis.
        instructions (Instructions): The instructions for the analysis.
        base_categories (list[str]): The base categories to include in the
            analysis.

    Returns:
        str: The instructions for the analysis.
    """
    result: str = instructions.base

    if "Characters" in categories:
        result += f"\n{instructions.character}"
    if "Settings" in categories:
        result += f"\n{instructions.settings}"

    if other_categories := [
        cat for cat in categories if cat not in base_categories
    ]:
        result += f"\nProvide descriptions of {', '.join(other_categories)}"
        result += " without referencing specific characters or plot points"

    return (
        result
        + "\nYou will format this information using the following schema where"
        + ' "description" is replaced with the actual information.\n'
    )


def initialize_instructions(instruction_type: str) -> Instructions:
    """
    Initializes the instructions dataclass for the analysis.

    Args:
        instruction_type (str): The type of instruction to use.

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


def create_role_script(
    categories: list[str],
    max_tokens: int,
    config: AnalyzerConfig,
    instructions: Instructions,
    added_character_traits: list[str] | None,
) -> RoleScript:
    """
    Creates the role script for the AI.

    Args:
        categories (list[str]): The categories to include in the analysis.
        max_tokens (int): The maximum number of tokens for the analysis.
        config (AnalyzerConfig): The configuration for the analysis.
        instructions (Instructions): The instructions for the analysis.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        RoleScript: The role script for the AI.
    """
    instruction_text: str = create_instructions(
        categories, instructions, config.base_categories
    )
    schema_text: str = "".join(
        generate_schema(
            category, added_character_traits, config.base_categories
        )
        for category in categories
    )
    return RoleScript(instruction_text + schema_text, max_tokens)


def build_role_scripts(
    chapter_data: dict,
    config: AnalyzerConfig,
    instructions: Instructions,
    added_character_traits: list[str] | None,
) -> list[RoleScript]:
    """
    Builds the role scripts for the AI.

    Args:
        chapter_data (dict): The data of the chapter.
        config (AnalyzerConfig): The configuration for the analysis.
        instructions (Instructions): The instructions for the analysis.
        added_character_traits (list[str] | None): The user added traits to
            include in the analysis.

    Returns:
        list[RoleScript]: The role scripts for the AI.
    """
    tokens_per: dict[str, int] = get_tokens_per(config.instruction_type)
    role_scripts: list[RoleScript] = []
    categories: list = []
    current_tokens: int = 0

    for category, names in chapter_data.items():
        category_tokens: int = min(
            len(names) * tokens_per.get(category, tokens_per["Other"]),
            config.absolute_max_tokens,
        )

        if (
            current_tokens + category_tokens > config.absolute_max_tokens
            and categories
        ):
            role_scripts.append(
                create_role_script(
                    categories,
                    current_tokens,
                    config,
                    instructions,
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
                config,
                instructions,
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
    if instruction_type == "json":
        from lorebinders.json_tools import RepairJSON

        return RepairJSON().json_str_to_dict(response)
    else:
        from lorebinders.markdown_parser import markdown_to_dict

        return markdown_to_dict(response)


def analyze_names(
    ai: AIInterface,
    metadata: BookDict,
    chapter: Chapter,
    config: AnalyzerConfig,
) -> dict:
    """
    Analyzes the names in the chapter and returns the analysis.

    Args:
        ai (AIInterface): The AIInterface object.
        metadata (BookDict): The metadata of the book.
        chapter (Chapter): The chapter to analyze.
        config (AnalyzerConfig): The configuration for the analysis.

    Returns:
        dict: The analysis of the names.

    """
    instructions: Instructions = initialize_instructions(
        config.instruction_type
    )
    role_scripts: list[RoleScript] = build_role_scripts(
        chapter_data=chapter.names,
        config=config,
        instructions=instructions,
        added_character_traits=metadata.character_traits,
    )

    responses: list[str] = [
        name_tools.get_ai_response(
            ai,
            script,
            f"Text: {chapter.text}",
            0.4,
            config.instruction_type == "json",
        )
        for script in role_scripts
    ]
    combined_response: str = combine_responses(
        responses=responses, json_mode=config.instruction_type == "json"
    )
    return parse_response(
        response=combined_response,
        instruction_type=config.instruction_type,
    )
