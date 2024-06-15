import re
from collections import defaultdict
from typing import Callable, List, Optional, Tuple

from data_cleaner import ManipulateData

data = ManipulateData()


class SortNames:
    """
    Class to sort and categorize names extracted from a response using AI
    model.

    Args:
        name_list (str): The raw NER response from the AI.
        narrator (str): The narrator's name if set.

    Attributes:
        ner_dict (defaultdict): A defaultdict to store categorized names.

    Methods:
        sort: Parse the raw NER string into a nested dictionary.
    """

    def __init__(self, name_list: str, narrator: Optional[str]) -> None:
        self._lines = name_list.split("\n")
        self._narrator = narrator or ""

        self.ner_dict: defaultdict = defaultdict(str)
        self._category_dict: dict = {}
        self._category_name: str = ""
        self._inner_values: list = []

        self._set_regex_patterns()

        self._junk_words: set = {
            "additional",
            "note",
            "none",
            "mentioned",
            "unknown",
            "he",
            "they",
            "she",
            "we",
            "it",
            "boy",
            "girl",
            "main",
            "him",
            "her",
            "I",
            "</s>",
            "a",
        }

    def _set_regex_patterns(self) -> None:
        """
        Compile regex patterns for various text processing needs.
        """
        self._not_int_ext_parenthetical_pattern = re.compile(
            r"\((?!interior|exterior).+\)$", re.IGNORECASE
        )
        self._inverted_setting_pattern = re.compile(
            r"(interior|exterior)\s+\((\w+)\)", re.IGNORECASE
        )
        self._leading_colon_pattern = re.compile(r"\s*:\s+")
        self._list_formatting_pattern = re.compile(
            r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t"
        )
        self._missing_newline_before_pattern = re.compile(
            r"(?<=\w)(?=[A-Z][a-z]*:)"
        )
        self._missing_newline_between_pattern = re.compile(
            r"(\w+ \(\w+\))\s+(\w+)"
        )
        self._missing_newline_after_pattern = re.compile(r"(?<=\w):\s*(?=\w)")

    def _missing_newline_patterns(self, line: str) -> list:
        """
        Apply patterns to add missing newlines to the line.
        """
        return [
            self._missing_newline_before_pattern.sub("\n", line),
            self._missing_newline_between_pattern.sub(r"\1\n\2", line),
            self._missing_newline_after_pattern.sub(":\n", line),
        ]

    def _lowercase_interior_exterior(self, line: str) -> str:
        """
        Lowercase 'interior' and 'exterior' in the line.
        """
        return re.sub(
            r"(interior|exterior)",
            lambda m: m.group().lower(),
            line,
            flags=re.IGNORECASE,
        )

    def _remove_leading_colon_pattern(self, line: str) -> str:
        """
        Remove leading colons from the line.
        """
        return self._leading_colon_pattern.sub("", line)

    def _remove_list_formatting(self, line: str) -> str:
        """
        Remove list formatting characters from the line.
        """
        return self._list_formatting_pattern.sub("", line)

    @staticmethod
    def _remove_parentheses(line: str) -> str:
        """
        Remove parentheses from the line.
        """
        return line.replace("(", "").replace(")", "")

    @staticmethod
    def _replace_bad_setting(line: str) -> str:
        """
        Replace invalid setting indicator with 'Settings:'.
        """
        return "Settings:"

    def _replace_inverted_setting(self, line: str) -> str:
        """
        Correct the order of inverted setting values in the line.
        """
        return self._inverted_setting_pattern.sub(r"\2 (\1)", line)

    def _remove_parantheticals_pattern(self, line: str) -> str:
        """
        Remove non-interior/exterior parantheticals from the line.
        """
        return self._not_int_ext_parenthetical_pattern.sub(r"\`1", line)

    @staticmethod
    def _num_added_lines(split_lines: list) -> int:
        """
        Calculate the number of added lines.
        """
        return len(split_lines) - 1

    def _add_missing_newline(self, line: str) -> Tuple[List[str], int]:
        """
        Add missing newlines to the line.

        Returns:
            split_lines (List[str]): A list of the split lines.
            (int): The number of lines to add to the index. This is one less
                than the total number of lines in split_lines.
        """
        patterns = self._missing_newline_patterns(line)
        for pattern in patterns:
            if pattern != line:
                split_lines = pattern.split("\n")
                num_added_lines = 1
                return split_lines, num_added_lines
        num_added_lines = 0
        return [line], num_added_lines

    def _split_at_commas(self, line: str) -> Tuple[List[str], int]:
        """
        Split the line at commas.

        Returns:
            split_lines (List[str]): A list of the split lines.
            (int): The number of lines to add to the index. This is one less
                than the total number of lines in split_lines.
        """
        split_lines = line.split(", ")
        return split_lines, self._num_added_lines(split_lines)

    def _split_settings_line(self, line: str) -> Tuple[List[str], int]:
        """
        Split settings line into individual place settings.

        Returns:
            split_lines (List[str]): A list of the split lines.
            (int): The number of lines to add to the index. This is one less
                than the total number of lines in split_lines.
        """
        prefix, places = line.split(":", 1)
        setting = "(interior)" if prefix == "interior" else "(exterior)"
        split_lines = [
            f"{place.strip()} {setting}" for place in places.split(",")
        ]
        return split_lines, self._num_added_lines(split_lines)

    @staticmethod
    def _ends_with_colon(line: str) -> bool:
        """
        Check if the line ends with a colon.
        """
        return line.endswith(":")

    @staticmethod
    def _has_bad_setting(line: str) -> bool:
        """
        Check if the line has a bad setting indicator.
        """
        return line.lower() in {
            "setting:",
            "location:",
            "locations:",
            "places:",
            "place:",
        }

    @staticmethod
    def _has_narrator(line: str) -> bool:
        """
        Check if the line mentions a narrator or main character.
        """
        return any(line.lower().split()) in {
            "narrator",
            "protagonist",
            "main character",
        }

    @staticmethod
    def _has_odd_parentheses(line: str) -> bool:
        """
        Check if the line has mismatched parentheses.
        """
        return line.count("(") != line.count(")")

    @staticmethod
    def _is_list_as_str(line: str) -> bool:
        """
        Check if the line is a list in string format.
        """
        return ", " in line

    @staticmethod
    def _should_compare_values(value_i: str, value_j: str) -> bool:
        """
        Determine if two values should be compared.
        """
        return (
            value_i != value_j
            and not value_i.endswith(")")
            and not value_j.endswith(")")
            and (value_i.startswith(value_j) or value_i.endswith(value_j))
        )

    def _should_skip_line(self, line: str) -> bool:
        """
        Determine if the line should be skipped based on junk words.
        """
        if line != "":
            line_set = set(line.lower().split())
            bool(line_set.intersection(self._junk_words))
        return True

    @staticmethod
    def _starts_with_location(line: str) -> bool:
        """
        Check if the line starts with a location indicator.
        """
        return line.startswith("interior:") or line.startswith("exterior:")

    def _add_to_dict(self, line: str) -> None:
        """
        Add the line to the category dictionary.
        """
        if self._ends_with_colon(line):
            if self._category_name:
                self._set_category_dict()
            self._category_name = line[:-1].title()
        else:
            self._inner_values.append(line)

    def _set_category_dict(self) -> None:
        """
        Set the category dictionary with the current category name and its
        corresponding inner values.        .
        """
        self._category_dict.setdefault(self._category_name, []).extend(
            self._inner_values
        )
        self._inner_values.clear()

    def _build_ner_dict(self) -> None:
        """
        Builds a Named Entity Recognition (NER) dictionary based on the
        categories and inner values stored in the category dictionary.

        This method iterates through the categories and inner values in the
        `_category_dict` dictionary. If a category name ends with 's' and its
        singular form exists in the `_category_dict`, it combines the inner
        values of both forms. It then compares and standardizes the names
        within the inner values using the `_compare_names` method. If
        standardized values are obtained, they are added to the `ner_dict`
        under the respective category name.

        Returns:
            None
        """
        name_map: dict = defaultdict(str)

        for category_name, inner_values in self._category_dict.items():
            if (
                category_name.endswith("s")
                and category_name[:-1] in self._category_dict
            ):
                inner_values.extend(self._category_dict[category_name[:-1]])
                self._category_dict[category_name[:-1]] = []

            if standardized_values := self._compare_names(
                inner_values, name_map
            ):
                self.ner_dict[category_name] = standardized_values

    def _compare_names(self, inner_values: list, name_map: dict) -> list:
        """
        Compares and standardizes names in the inner_values list.

        This method compares the names in the inner_values list and
        standardizes them based on certain conditions. It removes titles from
        the names using the _remove_titles method. Then, it iterates through
        each pair of names and checks if they are similar. If a pair of names
        is similar, it determines the singular and plural forms of the names
        and selects the shorter and longer values. It creates a name_map
        dictionary to map the shorter value to the longer value. Finally, it
        creates a set of standardized names by applying the name_map to each
        name in the inner_values list.

        Args:
            inner_values (list): A list of names to be compared and
                standardized.

        Returns:
            list: A list of standardized names.

        """
        cleaned_values = {
            value: data.remove_titles(value) for value in inner_values
        }
        name_map = {}

        for i, value_i in enumerate(inner_values):
            clean_i = cleaned_values[value_i]
            for value_j in inner_values[i+1:]:
                if self._should_compare_values(value_i, value_j):
                    clean_j = cleaned_values[value_j]
                    shorter_value, longer_value = self._sort_shorter_longer(
                        clean_i, clean_j
                    )
                    name_map[shorter_value] = longer_value

        standardized_names = {
            name_map.get(name, name) for name in inner_values
        }
        return list(standardized_names)

    @staticmethod
    def _sort_shorter_longer(clean_i: str, clean_j: str) -> Tuple[str, str]:
        """Get the shorter and longer of two cleaned names."""
        if clean_i == data.to_singular(clean_j):
            return clean_i, clean_j
        elif clean_j == data.to_singular(clean_i):
            return clean_j, clean_i
        else:
            shorter, longer = sorted([clean_i, clean_j], key=len)
            return shorter, longer

    def _split_and_update_lines(
        self, index: int, split_func: Callable[[str], Tuple[List[str], int]]
    ) -> int:
        """
        Split the line at index i using the provided split function and
        update the lines list.

        Args:
            index (int): The index of the line to split.
            lines (list[str]): The list of lines.
            split_func (Callable[[str], Tuple[list[str], int]]): The function
                to split the line.

        Returns:
            Tuple[int, bool]: A tuple containing the new index i and a
                boolean indicating whether to continue the main loop.
        """
        split_lines: List[str]
        added_lines: int

        split_lines, added_lines = split_func(self._lines[index])
        self._lines[index: index + 1] = split_lines
        return index + added_lines

    def sort(self) -> dict:
        """
        Parses the response from the AI model to extract names and add them to
        the Chapter object.

        This method takes the response from the AI model as input and extracts
        the names using the _sort_names method. It also retrieves the narrator
        from the Book object. The extracted names are then added to the
        Chapter object using the add_names method.

        Args:
            name_list (str): The response from the AI model.
            narrator (str): The narrator from the Book object.

        Returns:
            dict: A dictionary containing the sorted names categorized by
                their respective categories.
        """
        split_conditions = [
            (self._is_list_as_str, self._split_at_commas),
            (self._missing_newline_patterns, self._add_missing_newline),
        ]

        i = 0
        while i < len(self._lines):
            line = self._lines[i].strip()
            line = self._remove_list_formatting(line)
            if self._starts_with_location(line):
                i = self._split_and_update_lines(i, self._split_settings_line)
                continue
            line = self._lowercase_interior_exterior(line)
            line = self._replace_inverted_setting(line)
            for condition, split_func in split_conditions:
                if condition(line):
                    i = self._split_and_update_lines(i, split_func)
                    continue
            line = self._remove_leading_colon_pattern(line)
            if self._should_skip_line(line):
                i += 1
                continue
            if self._has_odd_parentheses(line):
                line = self._remove_parentheses(line)
            if self._has_bad_setting(line):
                line = self._replace_bad_setting(line)
            if self._has_narrator(line):
                line = self._narrator
            # line = self._remove_parantheticals_pattern(line)

            # Remaining lines ending with a colon are category names and lines
            # following belong in a list for that category
            self._add_to_dict(line)
            i += 1

        if self._category_name:
            self._set_category_dict()
        if self._category_dict:
            self._build_ner_dict()

        return self.ner_dict
