from abc import ABC, abstractmethod
import json
import re
from collections import defaultdict
from typing import List, Tuple

from _types import Book, Chapter
from _titles import TITLES
from ai_classes.openai_class import OpenAIAPI
from data_cleaner import DataCleaner
from json_repair import JSONRepair

data_cleaning = DataCleaner()
json_repair = JSONRepair()

class Names(ABC):
    """
    Abstract class for name classes
    """

    def __init__(self, book: Book) -> None:
        """
        Initialize the Names class with a Book object and an instance of the
        OpenAIAPI class.

        Args:
            book (Book): The Book object representing the book.

        Raises:
            TypeError: If book is not an instance of the Book class.
        """
        if not isinstance(book, Book):
            raise TypeError("book must be an instance of the Book class")
        self.book = book
        self.ai = OpenAIAPI(files=book.file_handler, errors=book.error_handler, model_key=self.model)

    def _call_ai(self) -> None:
        """
        Iterate over the Chapter objects stored in the Book object, send the
        text as prompts to the AI model, and fetch the response. For use with
        simpler prompts.
        """
        for Chapter.number, Chapter.text in self.book.chapters:
            prompt = f"Text: {Chapter.text}"
            api_payload = self.ai.create_payload(prompt, self._build_role_script(), self.temperature, self.max_tokens)
            response = self.ai.call_api(api_payload)
            self._clean_names(response)

    @abstractmethod
    def _parse_response(self, response: str) -> None:
        """
        Abstract method to parse the AI response.

        Args:
            response (str): The AI response.

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError("Method _parse_response must be implemented in child class.")

    @abstractmethod
    def _build_role_script(self) -> str:
        """
        Abstract method to build the role script.

        Returns:
            str: The role script.

        Raises:
            NotImplementedError: If the method is not implemented in the child
                class.
        """
        raise NotImplementedError("Method _build_role_script must be implemented in child class.")

class NameExtractor():
    """
    Responsible for extracting characters, settings, and other categories from
    the chapter text using Named Entity Recognition (NER).
    """
    def __init__(self, book: Book) -> None:
        super().__init__()

        self.model: str = "gpt_three"
        self.max_tokens: int = 1000
        self.temperature: float = 0.2

        self.custom_categories = book.custom_categories

    def _build_custom_role(self) -> str:
        if len(self.custom_categories) > 0:
            name_strings: list = []
            for name in self.custom_categories:
                attr: str = name.strip()
                name_string: str = f"{attr}:{attr}1, {attr}2, {attr}3"
                name_strings.append(name_string)
                role_categories: str = "\n".join(name_strings)
        return role_categories or ""
    
    def _build_role_script(self) -> None:
        role_categories: str = self._build_custom_role()
        self.role_script: str = (
            f"You are a script supervisor compiling a list of characters in each scene. "
            f"For the following selection, determine who are the characters, giving only "
            f"their name and no other information. Please also determine the settings, "
            f"both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, "
            f"Kastea, Hell's Kitchen).{self.custom_categories}.\n"
            f"If the scene is written in the first person, try to identify the narrator by "
            f"their name. If you can't determine the narrator's identity. List 'Narrator' as "
            f"a character. Use characters' names instead of their relationship to the "
            f"narrator (e.g. 'Uncle Joe' should be 'Joe'. If the character is only identified "
            f"by their relationship to the narrator (e.g. 'Mom' or 'Grandfather'), list the "
            f"character by that identifier instead of the relationship (e.g. 'Mom' instead of "
            f"'Narrator's mom' or 'Grandfather' instead of 'Kalia's Grandfather'\n"
            f"Be as brief as possible, using one or two words for each entry, and avoid "
            f"descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris "
            f"field of leftover asteroid pieces' should be 'Asteroid debris field'. 'Unmarked "
            f"section of wall (potentially a hidden door)' should be 'unmarked wall section' "
            f"Do not use these examples unless they actually appear in the text.\n"
            f"If you cannot find any mention of a specific category in the text, please "
            f"respond with 'None found' on the same line as the category name. If you are "
            f"unsure of a setting or no setting is shown in the text, please respond with "
            f"'None found' on the same line as the word 'Setting'\n"
            f"Please format the output exactly like this:\n"
            f"Characters:\n"
            f"character1\n"
            f"character2\n"
            f"character3\n"
            f"Settings:\n"
            f"Setting1 (interior)\n"
            f"Setting2 (exterior)\n"
            f"{role_categories}"
        )

    def extract_names(self) -> None:
        """
        Takes a Chapter object and extracts the names using an AI API.
        """
        self.role_script: str = self._build_role_script
        self._call_ai()
    
    def _parse_response(self, response: str) -> None:
        narrator = self.book.get("narrator")
        names = self._sort_names(response, narrator)
        Chapter.add_names(names)

    def _sort_names(self, name_list: str, narrator: str) -> dict:

        name_map: dict = {}
        name_table: dict = {}
        inner_dict: dict = {}
        category_name = None
        inner_values: dict = []

        character_info_pattern = re.compile(r"\((?!interior|exterior).+\)$", re.IGNORECASE)
        inverted_setting_pattern = re.compile(r"(interior|exterior)\s+\((\w+)\)", re.IGNORECASE)
        leading_colon_pattern = re.compile(r"\s*:\s+")
        list_formatting_pattern = re.compile(r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t")
        missing_newline_before_pattern = re.compile(r"(?<=\w)(?=[A-Z][a-z]*:)")
        missing_newline_between_pattern = re.compile(r"(\w+ \(\w+\))\s+(\w+)")
        missing_newline_after_pattern = re.compile(r"(?<=\w):\s*(?=\w)")
        junk: set = {"additional", "note", "none", "mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main", "him", "her", "I", "</s>", "a"}

        lines = name_list.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]
            line = list_formatting_pattern.sub("", line)
            line = re.sub(r'(interior|exterior)', lambda m: m.group().lower(), line, flags=re.IGNORECASE)
            if line.startswith("interior:") or line.startswith("exterior:"):
                prefix, places = line.split(":", 1)
                setting = "(interior)" if prefix == "interior" else "(exterior)"
                split_lines = [f"{place.strip()} {setting}" for place in places.split(",")]
                lines[i:i + 1] = split_lines
                continue
            line = inverted_setting_pattern.sub(r"\2 (\1)", line)
            if ", " in line:
                comma_split = line.split(", ")
                lines[i:i + 1] = comma_split
                continue
            added_newline = missing_newline_before_pattern.sub("\n", line)
            if added_newline != line:
                added_newlines = added_newline.split("\n")
                lines[i: i + 1] = added_newlines
                continue
            added_newline = missing_newline_between_pattern.sub(r"\1\n\2", line)
            if added_newline != line:
                added_newlines = added_newline.split("\n")
                lines[i: i + 1] = added_newlines
                continue
            added_newline = missing_newline_after_pattern.sub(":\n", line)
            if added_newline != line:
                added_newlines = added_newline.split("\n")
                lines[i: i + 1] = added_newlines
                continue
            line = leading_colon_pattern.sub("", line)
            line = line.strip()
            if line == "":
                i += 1
                continue
            if any(line.lower().split() in junk):
                i += 1
                continue
            if line.count("(") != line.count(")"):
                line.replace("(", "").replace(")", "")
            if line.lower() == "setting:":
                line = "Settings:"
            if any(line.lower().split()) in {"narrator", "protagonist", "main characater"}:
                line = narrator
            line = character_info_pattern.sub("", line)

            #Remaining lines ending with a colon are category names and lines following belong in a list for that category
            if line.endswith(":"):
                if category_name:
                    inner_dict.setdefault(category_name, []).extend(inner_values)
                    inner_values = []
                category_name = line[:-1].title()
            else:
                inner_values.append(line)
            i += 1

        if category_name:
            inner_dict.setdefault(category_name, []).extend(inner_values)
            inner_values = []
        if inner_dict:
            for category_name, inner_values in inner_dict.items():
                if category_name.endswith("s") and category_name[:-1] in inner_dict:
                    inner_values.extend(inner_dict[category_name[:-1]])
                    inner_dict[category_name[:-1]] = []
                inner_values = self._compare_names(inner_values, name_map)
                name_table[category_name] = inner_values
            inner_values = []
        # Remove empty category_name keys
        for category_name, inner_values in list(name_table.items()):
            if not inner_values:
                del name_table[category_name]
            return name_table

    def _compare_names(self, inner_values: list, name_map: dict) -> list:

        cleaned_values = {value: self._remove_titles(value) for value in inner_values}
        for i, value_i in enumerate(inner_values):
            clean_i = cleaned_values[value_i]

            for j, value_j in enumerate(inner_values):
                if i != j and value_i != value_j and not value_i.endswith(")") and not value_j.endswith(")") and (value_i.startswith(value_j) or value_i.endswith(value_j)):
                    clean_j = cleaned_values[value_j]
                    plural = None
                    singular = None
                    if clean_i == data_cleaning.to_singular(clean_j):
                        plural, singular = clean_j, clean_i
                    elif clean_j == data_cleaning.to_singular(clean_i):
                        plural, singular = clean_i, clean_j
                    if singular and plural:
                        shorter_value, longer_value = sorted([clean_i, clean_j], key = lambda x: plural if x == singular else x)
                    else:
                        shorter_value, longer_value = sorted([clean_i, clean_j], key = len)
                    name_map = defaultdict(lambda: longer_value)
                    name_map[shorter_value] = longer_value
        standardized_names = {name_map.get(name, name) for name in inner_values}
        return list(standardized_names)

    def _remove_titles(self, value: str) -> str:
        value_split: str = value.split()
        if value_split[0] in TITLES and value not in TITLES:
            return " ".join(value_split[1:])

class NameAnalyzer(Names):
    """
    Responsible for analyzing the extracted names to gather detailed
    information, such as descriptions, relationships, and locations.
    """
    def __init__(self, book: Book) -> None:
        super().__init__()
        
        self.model: str = "gpt_four"        
        self.temperature: float = 0.4
        
        self.custom_categories: list = book.custom_categories
        self.character_attributes: list = book.character_attributes
        
    def _generate_schema(self) -> str:
        """Generates a string representation of the JSON schema for the AI to follow"""
        
        self.categories_base = ["Characters", "Settings"]
        categories = self.categories_base + self.custom_categories
        
        character_attributes = ["Appearance", "Personality", "Mood", "Relationships with other characters"]
        character_attributes.extend(self.character_attributes)
        
        settings_attributes = ["Appearance", "Relative location", "Familiarity for main character"]
        
        cat_attr_map = {
            "Characters": character_attributes,
            "Settings": settings_attributes
            }
            
        schema: dict = {}
        
        for category in categories:
            if category in self.categories_base:
                schema_stub: dict = {category: "Description" for category in cat_attr_map[category]}
            else:
                schema_stub: str = "Description"
            schema[category] = schema_stub
            
        return json.dumps(schema)

    def _create_instructions(self, to_batch: list) -> str:

        instructions = (
            'You are a developmental editor helping create a story bible. \n'
            'Be detailed but concise, using short phrases instead of sentences. Do not '
            'justify your reasoning or provide commentary, only facts. Only one category '
            'per line, just like in the schema below, but all description for that '
            'category should be on the same line. If something appears to be '
            'miscatagorized, please put it under the correct category. USE ONLY STRINGS '
            'AND JSON OBJECTS, NO JSON ARRAYS. The output must be valid JSON.\n'
            'If you cannot find any mention of something in the text, please '
            'respond with "None found" as the description for that category. \n'
        )
        character_instructions = (
            'For each character in the chapter, describe their appearance, personality, '
            'mood, relationships to other characters, known or apparent sexuality.\n'
            'An example from an early chapter of Jane Eyre:\n'
            '"Jane Eyre": {"Appearance": "Average height, slender build, fair skin, '
            'dark brown hair, hazel eyes, plain apearance", "Personality": "Reserved, '
            'self-reliant, modest", "Mood": "Angry at her aunt about her treatment while '
            'at Gateshead"}'
        )
        setting_instructions = (
            'For each setting in the chapter, note how the setting is described, where '
            'it is in relation to other locations and whether the characters appear to be '
            'familiar or unfamiliar with the location. Be detailed but concise.\n'
            'If you are unsure of a setting or no setting is shown in the text, please '
            'respond with "None found" as the description for that setting.\n'
            'Here is an example from Wuthering Heights:\n'
            '"Moors": {"Appearance": Expansive, desolate, rugged, with high winds and '
            'cragy rocks", "Relative location": "Surrounds Wuthering Heights estate", '
            '"Main character\'s familiarity": "Very familiar, Catherine spent significant '
            'time roaming here as a child and represents freedom to her"}'
        )

        for category in to_batch:
            if category == "Characters":
                instructions += character_instructions
            if category == "Settings":
                instructions += setting_instructions
            else:
                other_category_list = [cat for cat in to_batch if cat not in self.categories_base]
                instructions += (
                    'Provide descriptons of ' +
                    ', '.join(other_category_list) +
                    ' without referencing specific characters or plot points\n'
                )

        instructions += (
            'You will format this information as a JSON object using the folllowing schema '
            'where "description" is replaced with the actual information.\n'
        )
        return instructions

    def _form_schema(self, to_batch: list) -> str:

        attributes_json = ""

        for category in to_batch:
            schema_json = self._generate_schema(category)
            attributes_json += schema_json

        return attributes_json

    def _reset_variables(self, category: str, token_count: int) -> Tuple[list, int]:

        to_batch = [category]
        max_tokens = token_count
        return to_batch, max_tokens

    def _append_attributes_batch(self, attributes_batch: list, to_batch: list, max_tokens: int, instructions: str) -> list:

        attributes_json: str = self._form_schema(to_batch)
        attributes_batch.append((attributes_json, max_tokens, instructions))
        return attributes_batch

    def _build_role_script(self) -> List[Tuple[str, int]]:
        """
        Build a list of tuples containing the role script and max_tokens to be used for each pass of the Chapter"
        """
        ABSOLUTE_MAX_TOKENS: int = 4096

        max_tokens: int = 0
        attributes_batch: list = []
        to_batch: list = []
        role_script_info: list = []

        tokens_per: dict = {
            "Characters": 200,
            "Settings": 150,
            "Other": 100
        }

        chapter_data: dict = Chapter.names
        
        for category, names in chapter_data.items():
            token_value = tokens_per.get(category, tokens_per["Other"])
            token_count = min(len(names) * token_value, ABSOLUTE_MAX_TOKENS)
            instructions = self._create_instructions(to_batch)
            if max_tokens + token_count > ABSOLUTE_MAX_TOKENS:
                instructions = self._create_instructions(to_batch)
                attributes_batch = self._append_attributes_batch(
                    attributes_batch,
                    to_batch,
                    max_tokens,
                    instructions
                )
                to_batch, max_tokens = self._reset_variables(category, token_count)
            else:
                to_batch.append(category)
                max_tokens += token_count

        if to_batch:
            instructions = self._create_instructions(to_batch)
            attributes_batch = self._append_attributes_batch(
                    attributes_batch, to_batch, max_tokens, instructions
                )

        for attributes_json, max_tokens, instructions in attributes_batch:
            role_script = (
                f'{instructions}'
                f'{attributes_json}'
            )
            role_script_info.append((role_script, max_tokens))
        return role_script_info
    
    def analyze_names(self) -> None:
        """
        Takes a chapter object and returns information about the names in its names list.
        """
        for Chapter.number, Chapter.text in self.book.chapters:
            prompt = f"Text: {Chapter.text}"
            role_script_info = self._build_role_script()
            
            response_whole: list = []
            for role_script, max_tokens in role_script_info:
                api_payload = self.ai.create_payload(prompt, role_script, self.temperature, max_tokens)
                response_part = self.ai.call_api(api_payload, json_response=True)
                response_whole.append(response_part)
            response = "{" + ",".join(part.lstrip("{").rstrip("}") for part in response_whole) + "}"

            self._parse_response(response)
            
    def _parse_response(self, response: str) -> None:
        """
        Loads the response as JSON, repairing it if necessary and adds it to
        the Chapter.
        
        Args:
            response (str): The response from the AI.
        
        Returns:
            None
        """
        parsed_response = json_repair.repair(response)
        Chapter.add_analysis(parsed_response)



class NameSummarizer():
    """
    Responsible for generating summaries for each name across all
    chapters.
    """
    def summarize_names(self, reshaped_data):
        """
        Takes the reshaped nested dictionary from DataReshaper and generates
        summaries for names using an AI API.
        Updates the nested dictionary with the summaries.
        """