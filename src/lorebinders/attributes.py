import json
from abc import ABCMeta, abstractmethod
from typing import Generator, List, Tuple, Union

from _types import AIModels, AIType, BookDict, Chapter
from ai_classes.ai_interface import AIInterface
from data_cleaner import ManipulateData
from json_repairer import JSONRepair
from sort_names import SortNames

data = ManipulateData()
json_repairer = JSONRepair()


class RoleScript:
    """
    Holds the AI system role script and max tokens for an API call
    """

    def __init__(self, script: str, max_tokens: int) -> None:
        self.script = script
        self.max_tokens = max_tokens


class AIModelConfig:
    def __init__(self, models: AIModels, model_id: int = 1) -> None:
        self._models = models
        self.provider = self._models.provider
        self._model_id = model_id

    def _model_key(self) -> None:
        self._key = self._models.models.get_model_by_id(self._model_id)

    def initialize_api(self) -> AIType:
        return AIInterface(self.provider, self._model_key)


class NameTools(metaclass=ABCMeta):
    """
    Abstract class for name classes
    """

    def __init__(
        self,
        metadata: BookDict,
        chapter: Chapter,
        ai_models: AIModels,
        model_id: int = 1,
    ) -> None:
        """
        Initialize the NameTools class with a Book object and an instance of
        the
        OpenAIAPI class.

        Args:
            chapter (Chapter): The Chapter object representing the chapter.

        Raises:
            TypeError: If book is not an instance of the Book class.
        """
        self.metadata = metadata
        self.chapter = chapter
        self._prompt = f"Text: {self.chapter.text}"

        self._ai_config = AIModelConfig(ai_models, model_id)
        self._ai = self._ai_config.initialize_api()

        self._categories_base = ["Characters", "Settings"]
        self._role_scripts: List[RoleScript] = []

    def get_info(self) -> str:
        """
        Iterate over the Chapter objects stored in the Book object, send the
        text as prompts to the AI model, and fetch the response. For use with
        simpler prompts.
        """

        responses = []
        for script in self._role_scripts:
            payload = self._ai.create_payload(script.script, script.max_tokens)
            response = self._ai.call_api(payload)
        if response:
            responses.append(response)
        return "".join(response)

    @abstractmethod
    def parse_response(self, response: str) -> Union[list, dict]:
        """
        Abstract method to parse the AI response.

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError(
            "Method _parse_response must be implemented in child class."
        )

    @abstractmethod
    def build_role_script(self) -> None:
        """
        Abstract method to build the role script

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError(
            "Method _build_role_script must be implemented in child class."
        )


class NameExtractor(NameTools):
    """
    Responsible for extracting characters, settings, and other categories from
    the chapter text using Named Entity Recognition (NER).
    """

    def __init__(
        self,
        metadata: BookDict,
        chapter: Chapter,
        ai_models: AIModels,
    ) -> None:
        super().__init__(metadata, chapter, ai_models)

        self.max_tokens: int = 1000
        self.temperature: float = 0.2

        self.narrator = self.metadata.narrator
        self.custom_categories = self.metadata.custom_categories

    def _build_custom_role(self) -> str:
        """
        Builds a custom role script based on the custom categories provided.

        Returns:
            str: The custom role script.

        """
        if len(self.custom_categories) > 0:
            name_strings: list = []
            for name in self.custom_categories:
                attr: str = name.strip()
                name_string: str = f"{attr}:{attr}1, {attr}2, {attr}3"
                name_strings.append(name_string)
                role_categories: str = "\n".join(name_strings)
        return role_categories or ""

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
        self._role_scripts = [
            RoleScript(
                (
                    "You are a script supervisor compiling a list of characters in "
                    "each scene. For the following selection, determine who are the "
                    "characters, giving only their name and no other information. "
                    "Please also determine the settings, both interior (e.g. ship's "
                    "bridge, classroom, bar) and exterior (e.g. moon, Kastea, Hell's "
                    f"Kitchen).{self.custom_categories}.\n"
                    "If the scene is written in the first person, try to identify "
                    "the narrator by their name. If you can't determine the "
                    "narrator's identity. List 'Narrator' as a character. Use "
                    "characters' names instead of their relationship to the narrator "
                    "(e.g. 'Uncle Joe' should be 'Joe'. If the character is only "
                    "identified by their relationship to the narrator (e.g. 'Mom' or "
                    "'Grandfather'), list the character by that identifier instead "
                    "of the relationship (e.g. 'Mom' instead of 'Narrator's mom' or "
                    "'Grandfather' instead of 'Kalia's Grandfather'\n"
                    "Be as brief as possible, using one or two words for each entry, "
                    "and avoid descriptions. For example, 'On board the Resolve' "
                    "should be 'Resolve'. 'Debris field of leftover asteroid pieces' "
                    "should be 'Asteroid debris field'. 'Unmarked section of wall "
                    "(potentially a hidden door)' should be 'unmarked wall section'\n"
                    "Do not use these examples unless they actually appear in the "
                    "text.\nIf you cannot find any mention of a specific category in "
                    "the text, please respond with 'None found' on the same line as "
                    "the category name. If you are unsure of a setting or no setting "
                    "is shown in the text, please respond with 'None found' on the "
                    "same line as the word 'Setting'\n"
                    "Please format the output exactly like this:\n"
                    "Characters:\n"
                    "character1\n"
                    "character2\n"
                    "character3\n"
                    "Settings:\n"
                    "Setting1 (interior)\n"
                    "Setting2 (exterior)\n"
                    f"{role_categories}"
                ),
                self.max_tokens,
            )
        ]

    def parse_response(self, response: str) -> dict:
        """
        Parses the response from the AI model to extract names and add them to
        the Chapter object.

        This method takes the response from the AI model as input and extracts
        the names using the _sort_names method. It also retrieves the narrator
        from the Book object. The extracted names are then added to the
        Chapter object using the add_names method.

        Argss:
            response (str): The response from the AI model.

        Returns:
            None
        """
        sorter = SortNames(response, self.narrator)
        return sorter.sort()


class NameAnalyzer(NameTools):
    """
    Responsible for analyzing the extracted names to gather detailed
    information, such as descriptions, relationships, and locations.

    Attributes:
        model (str): The AI model to be used for analysis.
        temperature (float): The temperature parameter for the AI model.
        custom_categories (list): A list of custom categories for analysis.
        character_attributes (list): A list of character attributes for
            analysis.

    Methods:
        _generate_schema: Generates a string representation of the JSON
            schema for the AI to follow.
        _create_instructions: Creates instructions for the AI based on the
            categories to be analyzed.
        _form_schema: Forms the JSON schema for the categories to be analyzed.
        _reset_variables: Resets the variables for a new batch of categories.
        _append_attributes_batch: Appends the attributes batch to the list.
        analyze_names: Analyzes the names in the chapters and returns
            information about them.
        _parse_response(: Parses the AI response and adds it to the Chapter.
    """

    def __init__(
        self,
        metadata: BookDict,
        chapter: Chapter,
        ai_models: AIModels,
        model_id: int = 3,
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
            character_attributes (list): A list of character attributes for
                analysis.
            categories_base (list): The base list of categories for analysis.

        Returns:
            None
        """
        super().__init__(metadata, chapter, ai_models)
        self.temperature: float = 0.4

        self.custom_categories: List[str] = self.metatada.custom_categories
        self.character_attributes: List[str] = (
            self.metadata.character_attributes
        )

    def _generate_schema(self, category: str) -> str:
        """
        Generates a string representation of the JSON schema for the AI to
        follow.

        This method is used to generate a JSON schema string that defines the
        structure and format of the data that the AI model will analyze for a
        given category.

        Args:
            cateogry (str): The category to form the JSON schema for.
        Returns:
            str: The JSON schema string.
        """

        character_attributes = [
            "Appearance",
            "Personality",
            "Mood",
            "Relationships with other characters",
        ]
        character_attributes.extend(self.character_attributes)

        settings_attributes = [
            "Appearance",
            "Relative location",
            "Familiarity for main character",
        ]

        cat_attr_map = {
            "Characters": character_attributes,
            "Settings": settings_attributes,
        }

        schema: dict = {}
        schema_stub: Union[dict, str]

        if category in self._categories_base:
            schema_stub = {
                category: "Description" for category in cat_attr_map[category]
            }
        else:
            schema_stub = "Description"
        schema[category] = schema_stub

        return json.dumps(schema)

    def _create_instructions(self, to_batch: list) -> str:
        """
        Creates instructions for the AI based on the categories to be
        analyzed.

        This method generates instructions for the AI model based on the
        categories that are going to be analyzed. The instructions provide
        guidance on how to describe characters and settings in the chapter. It
        also specifies the format in which the information should be provided,
        which is a JSON object.

        Args:
            to_batch (list): A list of categories to be analyzed.

        Returns:
            str: The instructions for the AI.
        """
        instructions = (
            "You are a developmental editor helping create a story bible. \n"
            "Be detailed but concise, using short phrases instead of "
            "sentences. Do not justify your reasoning or provide commentary, "
            "only facts. Only one category per line, just like in the schema "
            "below, but all description for that category should be on the "
            "same line. If something appears to be miscatagorized, please "
            "put it under the correct category. USE ONLY STRINGS AND JSON "
            "OBJECTS, NO JSON ARRAYS. The output must be valid JSON.\n"
            "If you cannot find any mention of something in the text, please "
            'respond with "None found" as the description for that'
            "category.\n"
        )
        character_instructions = (
            "For each character in the chapter, describe their appearance, "
            "personality, mood, and relationships to other characters\n"
            "An example from an early chapter of Jane Eyre:\n"
            '"Jane Eyre": {"Appearance": "Average height, slender build, fair '
            'skin, dark brown hair, hazel eyes, plain apearance", '
            '"Personality": "Reserved, self-reliant, modest", "Mood": "Angry '
            'at her aunt about her treatment while at Gateshead"}'
        )
        setting_instructions = (
            "For each setting in the chapter, note how the setting is "
            "described, where it is in relation to other locations and "
            "whether the characters appear to be familiar or unfamiliar with "
            "the location. Be detailed but concise.\n"
            "If you are unsure of a setting or no setting is shown in the "
            'text, please respond with "None found" as the description for '
            "that setting.\nHere is an example from Wuthering Heights:\n"
            '"Moors": {"Appearance": Expansive, desolate, rugged, with high '
            'winds and cragy rocks", "Relative location": "Surrounds '
            'Wuthering Heights estate", "Main character\'s familiarity": '
            '"Very familiar, Catherine spent significant time roaming here '
            'as a child and represents freedom to her"}'
        )

        for category in to_batch:
            if category == "Characters":
                instructions += character_instructions
            if category == "Settings":
                instructions += setting_instructions
            else:
                other_category_list = [
                    cat for cat in to_batch if cat not in self._categories_base
                ]
                instructions += (
                    "Provide descriptons of "
                    + ", ".join(other_category_list)
                    + " without referencing specific characters or plot points"
                )

        instructions += (
            "\nYou will format this information as a JSON object using the "
            'folllowing schema where "description" is replaced with the '
            "actual information.\n"
        )
        return instructions

    def _form_schema(self, to_batch: list) -> str:
        """
        Forms the JSON schema for the categories to be analyzed.

        This method takes a list of categories to be analyzed and generates a
        JSON schema string that defines the structure and format of the data
        that the AI model will analyze. It iterates over each category in the
        list and calls the `_generate_schema` method to generate the schema
        for that category. The generated schema strings are then concatenated
        together to form the final JSON schema.

        Args:
            to_batch (list): A list of categories to be analyzed.

        Returns:
            str: The JSON schema string.

        """
        attributes_json = ""

        for category in to_batch:
            schema_json = self._generate_schema(category)
            attributes_json += schema_json

        return attributes_json

    def _reset_variables(
        self, category: str, token_count: int
    ) -> Tuple[list, int]:
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
        to_batch = [category]
        max_tokens = token_count
        return to_batch, max_tokens

    def _append_attributes_batch(
        self,
        attributes_batch: list,
        to_batch: list,
        max_tokens: int,
        instructions: str,
    ) -> list:
        """
        Appends the attributes batch to the list.

        This method takes in an attributes batch, a list of categories to be
        analyzed, the maximum number of tokens, and the instructions for the
        AI. It generates the JSON schema for the categories using the
        _form_schema method. Then, it appends the attributes batch, consisting
        of the attributes JSON, the maximum tokens, and the instructions, to
        the list.

        Args:
            attributes_batch (list): The list of attributes batches.
            to_batch (list): A list of categories to be analyzed.
            max_tokens (int): The maximum number of tokens.
            instructions (str): The instructions for the AI.

        Returns:
            list: The updated attributes batch list.
        """
        attributes_json: str = self._form_schema(to_batch)
        attributes_batch.append((attributes_json, max_tokens, instructions))
        return attributes_batch

    def _build_role_script(self) -> List[Tuple[str, int]]:
        """
        Builds a list of tuples containing the role script and max_tokens to
        be used for each pass of the Chapter.

        Args:
            attributes_batch (list): The list of attributes batches.
            to_batch (list): A list of categories to be analyzed.
            max_tokens (int): The maximum number of tokens.
            instructions (str): The instructions for the AI.

        Returns:
            list: The updated attributes batch list.
        """
        ABSOLUTE_MAX_TOKENS: int = 4096

        max_tokens: int = 0
        attributes_batch: list = []
        to_batch: list = []
        role_script_info: list = []

        tokens_per: dict = {
            "Characters": 200,
            "Settings": 150,
            "Other": 100,
        }

        chapter_data: dict = Chapter.names

        for category, names in chapter_data.items():
            token_value = tokens_per.get(category, tokens_per["Other"])
            token_count = min(len(names) * token_value, ABSOLUTE_MAX_TOKENS)
            instructions = self._create_instructions(to_batch)
            if max_tokens + token_count > ABSOLUTE_MAX_TOKENS:
                instructions = self._create_instructions(to_batch)
                attributes_batch = self._append_attributes_batch(
                    attributes_batch, to_batch, max_tokens, instructions
                )
                to_batch, max_tokens = self._reset_variables(
                    category, token_count
                )
            else:
                to_batch.append(category)
                max_tokens += token_count

        if to_batch:
            instructions = self._create_instructions(to_batch)
            attributes_batch = self._append_attributes_batch(
                attributes_batch, to_batch, max_tokens, instructions
            )

        for attributes_json, max_tokens, instructions in attributes_batch:
            role_script = f"{instructions}" f"{attributes_json}"
            role_script_info.append((role_script, max_tokens))
        return role_script_info

    def analyze_names(self) -> None:
        """
        Takes a chapter object and returns information about the names in its
        names list.

        This method iterates over each chapter in the book and analyzes the
        names present in the chapter's text. It generates a prompt using the
        chapter's text and builds a role script using the _build_role_script
        method. The role script contains instructions and JSON schema for the
        AI model to follow. The method then calls the AI API for each role
        script in the role script info list and appends the responses to a
        list. Finally, it parses the response and adds the analyzed
        information to the Chapter object.
        """
        for chapter in self.book.get_chapters:
            prompt = f"Text: {chapter.text}"
            role_script_info = self._build_role_script()

            response_whole: list = []
            for role_script, max_tokens in role_script_info:
                api_payload = self._ai.create_payload(
                    prompt, role_script, self.temperature, max_tokens
                )
                response_part = self._ai.call_api(
                    api_payload, json_response=True
                )
                response_whole.append(response_part)
            response = (
                "{"
                + ",".join(
                    part.lstrip("{").rstrip("}") for part in response_whole
                )
                + "}"
            )

            self._parse_response(response, chapter)

    def _parse_response(self, response: str, chapter: Chapter) -> None:
        """
        Parses the AI response and adds it to the Chapter.

        This method takes in the AI response as a string and parses it using
        the JSONRepair class. The parsed response is then added to the Chapter
        object using the add_analysis method.

        Args:
            response (str): The AI response as a string.

        Returns:
            None
        """
        parsed_response = json_repairer.repair(response)
        if isinstance(parsed_response, dict):
            chapter.add_analysis(parsed_response)


class NameSummarizer(NameTools):
    """
    Responsible for generating summaries for each name across all
    chapters.


    Attributes:
        book (Book): The Book object representing the book.
        model_key (str): The key for the AI model to be used.
        temperature (float): The temperature parameter for AI response
            generation.
        max_tokens (int): The maximum number of tokens for AI response
            generation.
        role_script (str): The role script to be used for AI response
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
        self, metadata: BookDict, chapter: Chapter, ai_models: AIModels
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

        super().__init__(metadata, chapter, ai_models)
        self.temperature: float = 0.4
        self.max_tokens: int = 200

    def _build_role_script(self) -> None:
        self.role_script = (
            "You are an expert summarizer. Please summarize the description "
            "over the course of the story for the following:"
        )

    def _create_prompts(self) -> Generator:
        """
        Generate prompts for each name in the lorebinder.

        Yields:
            Tuple[str, str, str]: A tuple containing the category, name, and
                prompt for each name in the lorebinder.
        """

        for category, category_names in self.lorebinder.items():
            for name, chapters in category_names.items():
                for _, details in chapters.items():
                    if category in self._categories_base:
                        description = ", ".join(
                            f"{attribute}: {','.join(detail)}"
                            for attribute, detail in details.items()
                        )
                    else:
                        description = ", ".join(details)
                    yield (category, name, f"{name}: {description}")

    def sumarize_names(self) -> None:
        """
        Generate summaries for each name in the lorebinder.

        This method iterates over each name in the lorebinder and generates a
        summary using the OpenAI API. The generated summary is then parsed and
        updated in the lorebinder dictionary. Finally, the updated lorebinder
        is saved in the Book object.
        """
        self._build_role_script()
        for category, name, prompt in self._create_prompts():
            api_payload = self._ai.create_payload(
                prompt, self.role_script, self.temperature, self.max_tokens
            )
            response = self._ai.call_api(api_payload)
            self._parse_response(category, name, response)
        self.book.update_binder(self.lorebinder)

    def _parse_response(self, category: str, name: str, response: str) -> None:
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
            self.lorebinder[category][name]["summary"] = response
