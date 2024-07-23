from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import BookDict, Chapter

from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools import NameTools
from lorebinders.role_script import RoleScript


class NameAnalyzer(NameTools):
    """
    Responsible for analyzing the extracted names to gather detailed
    information, such as descriptions, relationships, and locations.

    Attributes:
        model (str): The AI model to be used for analysis.
        temperature (float): The temperature parameter for the AI model.
        custom_categories (list): A list of custom categories for analysis.
        character_traits (list): A list of character attributes for
            analysis.

    Methods:
        analyze_names: Analyzes the names in the chapters and returns
            information about them.
        parse_response(: Parses the AI response and adds it to the Chapter.
    """

    def __init__(
        self, ai: AIInterface, instruction_type: str, absolute_max_tokens: int
    ) -> None:
        """
        Initializes a NameAnalyzer object.

        Args:
            book (Book): The Book object representing the book.

        Raises:
            TypeError: If book is not an instance of the Book class.

        Attributes:
            model (str): The AI model to be used for analysis.
            temperature (float): The temperature parameter for the AI model.
            custom_categories (list): A list of custom categories for
                analysis.
            character_traits (list): A list of character attributes for
                analysis.
            categories_base (list): The base list of categories for analysis.

        Returns:
            None
        """
        super().__init__(ai)

        self.instruction_type = instruction_type
        self.absolute_max_tokens = absolute_max_tokens

        self.json_mode = self.instruction_type == "json"
        self.tokens_per = self._get_tokens_per()

        self._role_scripts: list[RoleScript] = []
        self.temperature: float = 0.4

        # Variables for lazy-loading instructions
        self._base_instructions: str | None = None
        self._character_instructions: str | None = None
        self._settings_instructions: str | None = None

    def _get_tokens_per(self) -> dict[str, int]:
        json_tokens = {"Characters": 200, "Settings": 150, "Other": 100}
        if self.instruction_type == "markdown":
            # markdown is 15% more token efficient than JSON
            return {k: int(v * 0.85) for k, v in json_tokens.items()}
        return json_tokens

    @property
    def base_instructions(self) -> str:
        """Lazy-loads base instructions."""
        if self._base_instructions is None:
            self._base_instructions = self._get_instruction_text(
                "name_analyzer_base_instructions.txt",
                prompt_type=self.instruction_type,
            )
        return self._base_instructions

    @property
    def character_instructions(self) -> str:
        """Lazy-loads character instructions."""
        if self._character_instructions is None:
            self._character_instructions = self._get_instruction_text(
                "character_instructions.txt", prompt_type=self.instruction_type
            )
        return self._character_instructions

    @property
    def settings_instructions(self) -> str:
        """Lazy-loads settings instructions."""
        if self._settings_instructions is None:
            self._settings_instructions = self._get_instruction_text(
                "settings_instructions.txt", prompt_type=self.instruction_type
            )
        return self._settings_instructions

    def initialize_chapter(self, metadata: BookDict, chapter: Chapter) -> None:
        self.metadata = metadata
        self.chapter = chapter

        self._prompt = f"Text: {self.chapter.text}"
        self.custom_categories = self.metadata.custom_categories
        self.character_traits = self.metadata.character_traits

    def _generate_schema(self, category: str) -> str:
        """
        Generates a string representation of the schema for the AI to
        follow.

        This method is used to generate a schema string that defines the
        structure and format of the data that the AI model will analyze for a
        given category.

        Args:
            category (str): The category to form the schema for.
        Returns:
            str: The schema string.
        """

        character_traits = [
            "Appearance",
            "Personality",
            "Mood",
            "Relationships with other characters",
        ]
        if self.character_traits:
            character_traits.extend(self.character_traits)

        schema_stub: dict | str

        if category in self._categories_base:
            settings_attributes = [
                "Appearance",
                "Relative location",
                "Familiarity for main character",
            ]

            cat_attr_map = {
                "Characters": character_traits,
                "Settings": settings_attributes,
            }

            schema_stub = {
                category: "Description" for category in cat_attr_map[category]
            }
        else:
            schema_stub = "Description"
        schema: dict = {category: schema_stub}
        return json.dumps(schema)

    def _create_instructions(self, categories: list[str]) -> str:
        """
        Creates instructions for the AI based on the categories to be
        analyzed.

        This method generates instructions for the AI model based on the
        categories that are going to be analyzed. The instructions provide
        guidance on how to describe characters and settings in the chapter. It
        also specifies the format in which the information should be provided.

        Args:
            to_batch (list): A list of categories to be analyzed.

        Returns:
            str: The instructions for the AI.
        """

        instructions = self.base_instructions
        other_category_list = [
            cat for cat in categories if cat not in self._categories_base
        ]

        if "Characters" in categories:
            instructions += f"\n{self.character_instructions}"
        if "Settings" in categories:
            instructions += f"\n{self.settings_instructions}"
        if other_category_list:
            instructions += (
                "\nProvide descriptions of "
                + ", ".join(other_category_list)
                + " without referencing specific characters or plot points"
            )

        instructions += (
            "\nYou will format this information using the following schema "
            'where "description" is replaced with the actual information.\n'
        )
        return instructions

    def _form_schema(self, categories: list) -> str:
        """
        Forms the schema for the categories to be analyzed.

        This method takes a list of categories to be analyzed and generates a
        schema string that defines the structure and format of the data
        that the AI model will analyze. It iterates over each category in the
        list and calls the `_generate_schema` method to generate the schema
        for that category. The generated schema strings are then concatenated
        together to form the final schema.

        Args:
            to_batch (list): A list of categories to be analyzed.

        Returns:
            str: The schema string.

        """
        attributes_str = ""

        for category in categories:
            schema_str = self._generate_schema(category)
            attributes_str += schema_str

        return attributes_str

    def build_role_script(self) -> None:
        """
        Builds a list of tuples containing the role script and max_tokens to
        be used for each pass of the Chapter.
        """

        chapter_data: dict = self.chapter.names

        categories: list[str] = []
        current_tokens = 0

        for category, names in chapter_data.items():
            token_value = self.tokens_per.get(
                category, self.tokens_per["Other"]
            )
            category_tokens = min(
                len(names) * token_value, self.absolute_max_tokens
            )

            if current_tokens + category_tokens > self.absolute_max_tokens:
                self._role_scripts.append(
                    self._create_role_script(categories, current_tokens)
                )
                categories = []
                current_tokens = 0

            categories.append(category)
            current_tokens += category_tokens

        if categories:
            self._role_scripts.append(
                self._create_role_script(categories, current_tokens)
            )

    def _create_role_script(
        self, categories: list[str], max_tokens: int
    ) -> RoleScript:
        """
        Creates a RoleScript object for the given categories.

        Args:
            categories (list[str]): List of categories to include in this
                RoleScript.
            max_tokens (int): Maximum number of tokens for this RoleScript.

        Returns:
            RoleScript: A RoleScript object.
        """
        instructions = self._create_instructions(categories)
        attributes_json = self._form_schema(categories)
        system_message = instructions + attributes_json
        return RoleScript(system_message, max_tokens)

    def _combine_responses(self, responses: list[str]) -> str:
        """Combine AI responses

        Args:
            responses (List[str]): A list of the AI responses as JSON strings.

        Returns:
            str: A stringified JSON array of the combined AI responses if JSON
            mode, or a string of the combined responses otherwise.
        """
        return (
            "{"
            + ",".join(part.lstrip("{").rstrip("}") for part in responses)
            + "}"
            if self.json_mode
            else "\n".join(responses)
        )

    def analyze_names(self) -> dict:
        responses: list[str] = []
        for script in self._role_scripts:
            response = self._get_ai_response(script, self._prompt)
            responses.append(response)
        combined_response = self._combine_responses(responses)
        return self._parse_response(combined_response)

    def _parse_response(self, response: str) -> dict:
        """
        Parses the AI response and adds it to the Chapter.

        This method takes in the AI response as a string and parses it using
        the JSONRepair class. The parsed response is then added to the Chapter
        object using the add_analysis method.

        Args:
            response (str): The AI response as a string.

        Returns:
            dict: The parsed response as a dictionary.
        """
        if self.instruction_type == "json":
            from lorebinders.json_tools import RepairJSON

            json_repair_tool = RepairJSON()
            return json_repair_tool.json_str_to_dict(response)
        else:
            from lorebinders.markdown_parser import markdown_to_dict

            return markdown_to_dict(response)
