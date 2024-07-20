from __future__ import annotations

import json
from typing import TYPE_CHECKING, Generator, cast

if TYPE_CHECKING:
    from lorebinders._types import BookDict, Chapter

from lorebinders.ai.ai_interface import AIInterface
from lorebinders.name_tools import NameTools
from lorebinders.role_script import RoleScript
from lorebinders.sort_names import SortNames


class NameExtractor(NameTools):
    """
    Responsible for extracting characters, settings, and other categories from
    the chapter text using Named Entity Recognition (NER).
    """

    def __init__(self, ai: AIInterface) -> None:
        super().__init__(ai)

        self.max_tokens: int = 1000
        self.temperature: float = 0.2

    def initialize_chapter(self, metadata: BookDict, chapter: Chapter) -> None:
        self.metadata = metadata
        self.chapter = chapter
        self._prompt = f"Text: {self.chapter.text}"
        self.narrator = self.metadata.narrator
        self.custom_categories = self.metadata.custom_categories
        self._base_instructions, self._further_instructions = (
            self._create_instructions()
        )

    def _create_instructions(self) -> tuple[str, str]:
        # TODO: Pass in instructions file path from config?
        base_instruction = self._get_instruction_text(
            "name_extractor_sys_prompt.txt"
        )
        further_instructions = self._get_instruction_text(
            "name_extractor_instructions.txt"
        )
        return base_instruction, further_instructions

    def _build_custom_role(self) -> str:
        """
        Builds a custom role script based on the custom categories provided.

        Returns:
            str: The custom role script.

        """
        role_categories: str = ""
        if self.custom_categories and len(self.custom_categories) > 0:
            name_strings: list = []
            for name in self.custom_categories:
                attr: str = name.strip()
                name_string: str = f"{attr}:{attr}1, {attr}2, {attr}3"
                name_strings.append(name_string)
                role_categories = "\n".join(name_strings)
        return role_categories

    def build_role_script(self) -> None:
        """
        Builds the role script for the NameExtractor class.

        This method constructs the role script that will be used by the
        NameExtractor class to extract characters and settings from the
        chapter text. The role script includes instructions for the AI, such
        as identifying characters and settings, handling first-person scenes,
        and formatting the output.

        Returns:
            None
        """
        role_categories: str = self._build_custom_role()

        system_message = (
            f"{self._base_instructions}\n{self.custom_categories}.\n"
            f"{self._further_instructions}\n{role_categories}"
        )
        self._single_role_script = RoleScript(system_message, self.max_tokens)

    def extract_names(self) -> dict:
        response = self._get_ai_response(
            self._single_role_script, self._prompt
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """
        Parses the response from the AI model to extract names and add them to
        the Chapter object.

        This method takes the response from the AI model as input and extracts
        the names using the _sort_names method. It also retrieves the narrator
        from the Book object. The extracted names are then added to the
        Chapter object using the add_names method.

        Args:
            response (str): The response from the AI model.

        Returns:
            dict: A dictionary containing the extracted names.
        """
        sorter = SortNames(response, self.narrator or "")
        return sorter.sort()


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


class NameSummarizer(NameTools):
    """
    Responsible for generating summaries for each name across all
    chapters.

    Attributes:
        metadata (dict): The book metadata.
        chapter (Chapter): The Chapter object being iterated over.
        temperature (float): The temperature parameter for AI response
            generation.
        max_tokens (int): The maximum number of tokens for AI response
            generation.
        _single_role_script (str): The role script to be used for AI response
            generation.
        lorebinder (dict): The lorebinder dictionary containing the names,
            categories, and summaries.

    Methods:
        __init__: Initialize the NameSummarizer class with a Book object.

        _create_prompts: Generate prompts for each name in the lorebinder.

        summarize_names: Generate summaries for each name in the lorebinder.

        _parse_response: Parse the AI response and update the lorebinder with
            the generated summary.
    """

    def __init__(self, ai: AIInterface) -> None:
        """
        Initialize the NameSummarizer class with a Book object.

        Args:
            ai (AIInterface): The AIInterface object.

        Attributes:
            temperature (float): The temperature parameter for AI response
                generation.
            max_tokens (int): The maximum number of tokens for AI response
                generation.
            _single_role_script (str): The role script to be used for AI
                response generation.

        Returns:
            None
        """

        super().__init__(ai)

        self.temperature: float = 0.4
        self.max_tokens: int = 200

        self._single_role_script: RoleScript | None = None

    def build_role_script(self) -> None:
        system_message = (
            "You are an expert summarizer. Please summarize the description "
            "over the course of the story for the following:"
        )
        self._single_role_script = RoleScript(system_message, self.max_tokens)

    def _create_prompts(self) -> Generator:
        """
        Generate prompts for each name in the lorebinder.

        Yields:
            Tuple[str, str, str]: A tuple containing the category, name, and
                prompt for each name in the lorebinder.
        """
        minimum_chapter_threshold = 3

        def create_description(category: str, details: dict | list) -> str:
            if category in self._categories_base:
                detail_dict: dict = cast(dict, details)  # Stupid MyPy
                return ", ".join(
                    f"{attribute}: {','.join(detail)}"
                    for attribute, detail in detail_dict.items()
                )
            else:
                detail_list: list = cast(list, details)
                return ", ".join(detail_list)

        def filter_chapters(category_names: dict) -> Generator:
            for name, chapters in category_names.items():
                if len(chapters) > minimum_chapter_threshold:
                    yield name, chapters

        def generate_prompts(category: str, category_names: dict) -> Generator:
            for name, chapters in filter_chapters(category_names):
                for _, details in chapters.items():
                    description = create_description(category, details)
                    yield category, name, f"{name}: {description}"

        for category, category_names in self.lorebinder.items():
            yield from generate_prompts(category, category_names)

    def summarize_names(self, lorebinder: dict) -> dict:
        """
        Generate summaries for each name in the Lorebinder.

        This method iterates over each name in the Lorebinder and generates a
        summary. The generated summary is then parsed and updated in the
        Lorebinder dictionary.
        """
        self.lorebinder = lorebinder
        for category, name, prompt in self._create_prompts():
            self._current_category = category
            self._current_name = name
            if self._single_role_script:
                response = self._get_ai_response(
                    self._single_role_script, prompt
                )
                self.lorebinder = self._parse_response(response)
        return self.lorebinder

    def _parse_response(self, response: str) -> dict:
        """
        Parse the AI response and update the lorebinder with the generated
        summary.

        This method takes the AI response as input and updates the lorebinder
        dictionary with the generated summary for a specific category and
        name. If the response is not empty, the summary is assigned to the
        corresponding category and name in the lorebinder.

        Args:
            category (str): The category of the name.
            name (str): The name for which the summary is generated.
            response (str): The AI response containing the generated summary.
        """
        if response:
            category = self._current_category
            name = self._current_name
            self.lorebinder[category][name]["summary"] = response
        return self.lorebinder
