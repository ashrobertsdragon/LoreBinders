from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Generator, cast

if TYPE_CHECKING:
    from lorebinders._types import BookDict, Chapter, RateLimitManager

import lorebinders.file_handling as file_handling
from lorebinders.ai.ai_models._model_schema import APIProvider
from lorebinders.json_tools import RepairJSON
from lorebinders.name_tools import NameTools
from lorebinders.role_script import RoleScript
from lorebinders.sort_names import SortNames

json_repair_tool = RepairJSON()


class NameExtractor(NameTools):
    """
    Responsible for extracting characters, settings, and other categories from
    the chapter text using Named Entity Recognition (NER).
    """

    def __init__(
        self,
        provider: APIProvider,
        rate_limiter: RateLimitManager,
        family: str,
    ) -> None:
        self.set_variables()
        self.initialize_api(provider, rate_limiter)
        self.set_family(family)
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
        base_instructions_file = os.path.join(
            "instructions",
            "name_extractor_sys_prompt.txt",
        )
        further_instructions_file = os.path.join(
            "instructions",
            "name_extractor_instructions.txt",
        )
        base_instructions: str = file_handling.read_text_file(
            base_instructions_file
        )
        further_instructions: str = file_handling.read_text_file(
            further_instructions_file
        )

        return base_instructions, further_instructions

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
        self,
        provider: APIProvider,
        rate_limiter: RateLimitManager,
        family: str,
        model_id: int,
        instruction_type: str,
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
        self.set_variables()
        self.initialize_api(provider, rate_limiter)
        self.set_family(family)
        self.set_model(model_id)

        self.instruction_type = instruction_type
        self.temperature: float = 0.4
        self._json_mode = self.instruction_type == "json"

        self.set_token_rules(family, model_id)

        # Initialize variables for batch processing
        self.max_tokens = 0
        self._attributes_batch: list[tuple[str, int, str]] = []
        self._to_batch: list = []
        self._role_scripts: list[RoleScript] = []

    def set_token_rules(self, family: str, model_id: int) -> None:
        model = get_model(family, model_id)
        self.absolute_max_tokens = model.absolute_max_tokens

        if self.instruction_type == "json":
            self.tokens_per: dict = {
                "Characters": 200,
                "Settings": 150,
                "Other": 100,
            }
        elif self.instruction_type == "markdown":
            self.tokens_per = {
                "Characters": 170,
                "Settings": 130,
                "Other": 85,
            }

    def _initialize_instructions(self) -> tuple[str, str, str]:
        # TODO: Pass in instructions file path from config?
        base_instructions = self._get_instruction_text(
            "name_analyzer_base_instructions.txt"
        )
        character_instructions = self._get_instruction_text(
            "character_instructions.txt"
        )
        settings_instructions = self._get_instruction_text(
            "settings_instructions.txt"
        )

        return base_instructions, character_instructions, settings_instructions

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

    def _get_instruction_text(self, file_name: str) -> str:
        """
        Reads the instructions file and returns the text.
        """
        file_path = os.path.join(
            "instructions", self.instruction_type, file_name
        )
        return file_handling.read_text_file(file_path)

    def _create_instructions(self) -> str:
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
        base_instructions, character_instructions, settings_instructions = (
            self._initialize_instructions()
        )

        for category in self._to_batch:
            if category == "Characters":
                instructions = base_instructions + character_instructions
            if category == "Settings":
                instructions += settings_instructions
            else:
                other_category_list = [
                    cat
                    for cat in self._to_batch
                    if cat not in self._categories_base
                ]
                instructions += (
                    "Provide descriptions of "
                    + ", ".join(other_category_list)
                    + " without referencing specific characters or plot points"
                )

        instructions += (
            "\nYou will format this information using the following schema "
            'where "description" is replaced with the actual information.\n'
        )
        return instructions

    def _form_schema(self) -> str:
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

        for category in self._to_batch:
            schema_str = self._generate_schema(category)
            attributes_str += schema_str

        return attributes_str

    def _reset_variables(self, category: str, token_count: int) -> None:
        """
        Resets the variables for a new batch of categories.

        This method takes in a category and a token count as input and resets
        the variables for a new batch of categories. It initializes the
        'to_batch' list with the given category and sets the 'max_tokens'
        variable to the token count.

        Args:
            category (str): The category for the new batch.
            token_count (int): The token count for the new batch.

        Returns:
            Tuple[list, int]: A tuple containing the updated 'to_batch' list
                and 'max_tokens' variable.

        """
        self._to_batch = [category]
        self.max_tokens = token_count

    def _append_attributes_batch(self, instructions: str) -> None:
        """
        Appends the attributes batch to the list.

        This method takes in an attributes batch, a list of categories to be
        analyzed, the maximum number of tokens, and the instructions for the
        AI. It generates the JSON schema for the categories using the
        _form_schema method. Then, it appends the attributes batch, consisting
        of the attributes JSON, the maximum tokens, and the instructions, to
        the list.

        Args:
            instructions (str): The instructions for the AI.

        Returns:
            list: The updated attributes batch list.
        """
        attributes_json: str = self._form_schema()
        self._attributes_batch.append((
            attributes_json,
            self.max_tokens,
            instructions,
        ))

    def build_role_script(self) -> None:
        """
        Builds a list of tuples containing the role script and max_tokens to
        be used for each pass of the Chapter.
        """

        chapter_data: dict = Chapter.names

        for category, names in chapter_data.items():
            token_value = self.tokens_per.get(
                category, self.tokens_per["Other"]
            )
            token_count = min(
                len(names) * token_value, self.absolute_max_tokens
            )
            instructions = self._create_instructions()
            if self.max_tokens + token_count > self.absolute_max_tokens:
                instructions = self._create_instructions()
                self._append_attributes_batch(instructions)
                self._reset_variables(category, token_count)
            else:
                self._to_batch.append(category)
                self.max_tokens += token_count

        if self._to_batch:
            instructions = self._create_instructions()
            self._append_attributes_batch(instructions)

        for (
            attributes_json,
            max_tokens,
            instructions,
        ) in self._attributes_batch:
            system_message = instructions + attributes_json
            role_script = RoleScript(system_message, max_tokens)
            self._role_scripts.append(role_script)

    def _combine_responses(self, responses: list[str]) -> str:
        """Combine AI responses

        Args:
            responses (List[str]): A list of the AI responses as JSON strings.

        Returns:
            str: A stringified JSON array of the combined AI responses.
        """
        return (
            "{"
            + ",".join(part.lstrip("{").rstrip("}") for part in responses)
            + "}"
            if self._json_mode
            else "".join(responses)
        )

    def analyze_names(self, model_id) -> dict:
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
            T
        """
        return json_repair_tool.json_str_to_dict(response)


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

    def __init__(
        self,
        provider: APIProvider,
        family: str,
        model_id: int,
        rate_limiter: RateLimitManager,
    ) -> None:
        """
        Initialize the NameSummarizer class with a Book object.

        Args:
            book (Book): The Book object representing the book.

        Raises:
            TypeError: If book is not an instance of the Book class.

        Returns:
            None
        """

        self.set_variables()
        self.initialize_api(provider, rate_limiter)
        self.set_family(family)
        self.set_model(model_id)

        self.temperature: float = 0.4
        self.max_tokens: int = 200

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
            response = self._get_ai_response(self._single_role_script, prompt)
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
