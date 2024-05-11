import re
from collections import defaultdict

from _types import Book, Chapter
from _titles import TITLES
from ai_classes.openai_class import OpenAIAPI
from data_cleaner import DataCleaner

data_cleaning = DataCleaner()

class AttributeExtractor():
    """
    Responsible for extracting characters, settings, and other attributes from
    the chapter text using Named Entity Recognition (NER).
    """
    def __init__(self, book: Book) -> None:
        self.custom_attributes = book.custom_attributes

        MODEL: str = "gpt_three"
        self.ai = OpenAIAPI(files=book.file_handler, errors=book.error_handler, model_key=MODEL)

        self.MAX_TOKENS: int = 1000
        self.TEMPERATURE: float = 0.2

    def _build_custom_role(self) -> str:
        if len(self.custom_attributes) > 0:
            attribute_strings: list = []
            for attribute in self.custom_attributes:
                attr: str = attribute.strip()
                attribute_string: str = f"{attr}:{attr}1, {attr}2, {attr}3"
                attribute_strings.append(attribute_string)
                role_attributes: str = "\n".join(attribute_strings)
        return role_attributes or ""
    
    def build_role_script(self) -> None:
        role_attributes: str = self._build_custom_role()
        self.role_script: str = (
            f"You are a script supervisor compiling a list of characters in each scene. "
            f"For the following selection, determine who are the characters, giving only "
            f"their name and no other information. Please also determine the settings, "
            f"both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, "
            f"Kastea, Hell's Kitchen).{self.custom_attributes}.\n"
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
            f"If you cannot find any mention of a specific attribute in the text, please "
            f"respond with 'None found' on the same line as the attribute name. If you are "
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
            f"{role_attributes}"
        )

    def extract_attributes(self, book: Book):
        """
        Takes a Chapter object and extracts the attributes using the OpenAI
        API. Returns a nested dictionary structure with the extracted data.
        """

        for Chapter["number"], Chapter.text in book.chapters:
            prompt = f"Text: {Chapter.text}"
            api_payload = self.ai.create_payload(prompt, self.role_script, self.TEMPERATURE, self.MAX_TOKENS)
            attribute_list = self.ai.call_api(api_payload)
            narrator = book.get("narrator")
            attributes = self._sort_names(attribute_list, narrator)
            Chapter.add_attributes(attributes)

    def _sort_names(self, attribute_list: str, narrator: str) -> dict:

        name_map: dict = {}
        attribute_table: dict = {}
        inner_dict: dict = {}
        attribute_name = None
        inner_values: dict = []

        character_info_pattern = re.compile(r"\((?!interior|exterior).+\)$", re.IGNORECASE)
        inverted_setting_pattern = re.compile(r"(interior|exterior)\s+\((\w+)\)", re.IGNORECASE)
        leading_colon_pattern = re.compile(r"\s*:\s+")
        list_formatting_pattern = re.compile(r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t")
        missing_newline_before_pattern = re.compile(r"(?<=\w)(?=[A-Z][a-z]*:)")
        missing_newline_between_pattern = re.compile(r"(\w+ \(\w+\))\s+(\w+)")
        missing_newline_after_pattern = re.compile(r"(?<=\w):\s*(?=\w)")
        junk: set = {"additional", "note", "none", "mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main", "him", "her", "I", "</s>", "a"}


        lines = attribute_list.split("\n")

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

            #Remaining lines ending with a colon are attribute names and lines following belong in a list for that attribute
            if line.endswith(":"):
                if attribute_name:
                    inner_dict.setdefault(attribute_name, []).extend(inner_values)
                    inner_values = []
                attribute_name = line[:-1].title()
            else:
                inner_values.append(line)
            i += 1

        if attribute_name:
            inner_dict.setdefault(attribute_name, []).extend(inner_values)
            inner_values = []
        if inner_dict:
            for attribute_name, inner_values in inner_dict.items():
                if attribute_name.endswith("s") and attribute_name[:-1] in inner_dict:
                    inner_values.extend(inner_dict[attribute_name[:-1]])
                    inner_dict[attribute_name[:-1]] = []
                inner_values = self._compare_names(inner_values, name_map)
                attribute_table[attribute_name] = inner_values
            inner_values = []
        # Remove empty attribute_name keys
        for attribute_name, inner_values in list(attribute_table.items()):
            if not inner_values:
                del attribute_table[attribute_name]
            return attribute_table

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

class AttributeAnalyzer():
    """
    Responsible for analyzing the extracted attributes to gather detailed
    information, such as descriptions, relationships, and locations.
    """
    def analyze_attributes(self, extracted_data):
        """
        Takes the nested dictionary from AttributeExtractor and analyzes the
        extracted attributes using an AI API.
        Updates the nested dictionary with the analyzed data.
        """


class AttributeSummarizer():
    """
    Responsible for generating summaries for each attribute across all
    chapters.
    """
    def summarize_attributes(self, reshaped_data):
        """
        Takes the reshaped nested dictionary from DataReshaper and generates
        summaries for attributes using an AI API.
        Updates the nested dictionary with the summaries.
        """