import re
from collections import defaultdict
from collections.abc import Callable

import lorebinders.data_cleaner as data_cleaner


class SortNames:
    """Class to sort and categorize names extracted from AI response.

    This class processes raw named entity recognition (NER) responses from
    AI models and sorts them into categorized dictionaries.

    Attributes:
        ner_dict: Dictionary to store categorized names.
    """

    def __init__(self, name_list: str, narrator: str | None = None) -> None:
        """Initialize the SortNames instance.

        Args:
            name_list: The raw NER response from the AI.
            narrator: The narrator's name if set.
        """
        self._lines = name_list.split("\n")
        self._narrator = narrator or ""

        self.ner_dict: dict = {}
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
        """Compile regex patterns for various text processing needs."""
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
        """Apply patterns to add missing newlines to the line.

        Args:
            line: The line to process.

        Returns:
            List of processed line variations.
        """
        return [
            self._missing_newline_before_pattern.sub("\n", line),
            self._missing_newline_between_pattern.sub(r"\1\n\2", line),
            self._missing_newline_after_pattern.sub(":\n", line),
        ]

    @staticmethod
    def _lowercase_interior_exterior(line: str) -> str:
        """Lowercase 'interior' and 'exterior' in the line.

        Args:
            line: The line to process.

        Returns:
            Line with lowercased interior/exterior words.
        """
        return re.sub(
            r"(interior|exterior)",
            lambda m: m.group().lower(),
            line,
            flags=re.IGNORECASE,
        )

    def _remove_leading_colon_pattern(self, line: str) -> str:
        """Remove leading colons from the line.

        Args:
            line: The line to process.

        Returns:
            Line with leading colons removed.
        """
        return self._leading_colon_pattern.sub("", line)

    def _remove_list_formatting(self, line: str) -> str:
        """Remove list formatting characters from the line.

        Args:
            line: The line to process.

        Returns:
            Line with list formatting removed.
        """
        return self._list_formatting_pattern.sub("", line)

    @staticmethod
    def _remove_parentheses(line: str) -> str:
        """Remove parentheses from the line.

        Args:
            line: The line to process.

        Returns:
            Line with parentheses removed.
        """
        return line.replace("(", "").replace(")", "")

    @staticmethod
    def _replace_bad_setting() -> str:
        """Replace invalid setting indicator with 'Settings:'.

        Returns:
            String 'Settings:' as replacement.
        """
        return "Settings:"

    def _replace_inverted_setting(self, line: str) -> str:
        """Correct the order of inverted setting values in the line.

        Args:
            line: The line to process.

        Returns:
            Line with corrected setting order.
        """
        return self._inverted_setting_pattern.sub(r"\2 (\1)", line)

    def _remove_parantheticals_pattern(self, line: str) -> str:
        """Remove non-interior/exterior parantheticals from the line.

        Args:
            line: The line to process.

        Returns:
            Line with non-interior/exterior parentheticals removed.
        """
        return self._not_int_ext_parenthetical_pattern.sub(r"\1", line)

    @staticmethod
    def _num_added_lines(split_lines: list) -> int:
        """Calculate the number of added lines.

        Args:
            split_lines: List of split lines.

        Returns:
            Number of lines added (length - 1).
        """
        return len(split_lines) - 1

    def _needs_newline(self, line: str) -> bool:
        """Check if the line needs a newline based on the patterns.

        Args:
            line (str): The line to check.

        Returns:
            bool: True if any pattern matches, False otherwise.
        """
        patterns = self._missing_newline_patterns(line)
        return any(pattern != line for pattern in patterns)

    def _add_missing_newline(self, line: str) -> tuple[list[str], int]:
        """Add missing newlines to the line.

        Args:
            line (str): The line to check.

        Returns:
            Tuple[list[str], int]: A list of the split lines and the number of
            lines that were added to the original.
        """
        patterns = self._missing_newline_patterns(line)
        return next(
            (
                (pattern.split("\n"), 1)
                for pattern in patterns
                if pattern != line
            ),
            ([line], 0),
        )

    def _split_at_commas(self, line: str) -> tuple[list[str], int]:
        """Split the line at commas.

        Args:
            line: The line to split.

        Returns:
            Tuple of split lines and number of lines added.
        """
        split_lines = line.split(", ")
        return split_lines, self._num_added_lines(split_lines)

    def _split_settings_line(self, line: str) -> tuple[list[str], int]:
        """Split settings line into individual place settings.

        Args:
            line: The settings line to split.

        Returns:
            Tuple of split lines and number of lines added.
        """
        prefix, places = line.split(":", 1)
        setting = "(interior)" if prefix == "interior" else "(exterior)"
        split_lines = [
            f"{place.strip()} {setting}" for place in places.split(",")
        ]
        return split_lines, self._num_added_lines(split_lines)

    @staticmethod
    def _ends_with_colon(line: str) -> bool:
        """Check if the line ends with a colon.

        Args:
            line: The line to check.

        Returns:
            True if line ends with colon, False otherwise.
        """
        return line.endswith(":")

    @staticmethod
    def _has_bad_setting(line: str) -> bool:
        """Check if the line has a bad setting indicator.

        Args:
            line: The line to check.

        Returns:
            True if line has bad setting indicator, False otherwise.
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
        """Check if the line mentions a narrator or main character.

        Args:
            line: The line to check.

        Returns:
            True if line mentions narrator/main character, False otherwise.
        """
        narrator_phrases = ["narrator", "protagonist", "main character"]
        return any(phrase in line.lower() for phrase in narrator_phrases)

    @staticmethod
    def _has_odd_parentheses(line: str) -> bool:
        """Check if the line has mismatched parentheses.

        Args:
            line: The line to check.

        Returns:
            True if parentheses are mismatched, False otherwise.
        """
        return line.count("(") != line.count(")")

    @staticmethod
    def _is_list_as_str(line: str) -> bool:
        """Check if the line is a list in string format.

        Args:
            line: The line to check.

        Returns:
            True if line contains comma-separated values, False otherwise.
        """
        return ", " in line

    @staticmethod
    def _should_compare_values(value_i: str, value_j: str) -> bool:
        """Determine if two values should be compared.

        Args:
            value_i: First value to compare.
            value_j: Second value to compare.

        Returns:
            True if values should be compared, False otherwise.
        """
        return (
            value_i != value_j
            and not value_i.endswith(")")
            and not value_j.endswith(")")
            and (value_i.startswith(value_j) or value_i.endswith(value_j))
        )

    def _should_skip_line(self, line: str) -> bool:
        """Determine if the line should be skipped based on junk words.

        Args:
            line: The line to check.

        Returns:
            True if line should be skipped, False otherwise.
        """
        if line != "":
            line_set = set(line.lower().split())
            return not line_set.isdisjoint(self._junk_words)
        return True

    @staticmethod
    def _starts_with_location(line: str) -> bool:
        """Check if the line starts with a location indicator.

        Args:
            line: The line to check.

        Returns:
            True if line starts with interior: or exterior:, False otherwise.
        """
        return line.startswith("interior:") or line.startswith("exterior:")

    def _add_to_dict(self, line: str) -> None:
        """Add the line to the category dictionary.

        Args:
            line: The line to add to the dictionary.
        """
        if self._ends_with_colon(line):
            if self._category_name:
                self._set_category_dict()
            self._category_name = line[:-1].title()
        else:
            self._inner_values.append(line)

    def _set_category_dict(self) -> None:
        """Set category dictionary with current category name and values."""
        self._category_dict.setdefault(self._category_name, []).extend(
            self._inner_values
        )
        self._inner_values.clear()

    def _combine_singular_to_plural(self, category_name: str) -> list:
        """Combine singular and plural forms of the category name.

        Args:
            category_name (str): The name of the category to combine.

        Returns:
            list: A list of combined category names.
        """
        inner_values: list[str] = []
        if category_name.endswith("s"):
            inner_values = self._category_dict[category_name]
            singular_key = category_name[:-1]
            if singular_key in self._category_dict:
                inner_values = self._category_dict[category_name]
                inner_values.extend(self._category_dict[singular_key])
                self._category_dict[singular_key] = []

        return inner_values

    def _build_ner_dict(self) -> dict[str, list[str]]:
        """Build a Named Entity Recognition (NER) dictionary.

        Iterates through categories and inner values in the category
        dictionary. Combines singular and plural forms, then compares and
        standardizes names within the inner values.

        Returns:
            Dictionary containing categorized and standardized names.
        """
        ner_dict: dict[str, list[str]] = {}
        for category_name, inner_values in list(self._category_dict.items()):
            if inner_values := self._combine_singular_to_plural(category_name):
                standardized_values = self._compare_names(inner_values)
                ner_dict[category_name] = standardized_values
        return ner_dict

    def _compare_names(self, inner_values: list) -> list:
        """Compare and standardize names in the inner_values list.

        Removes titles from names, compares pairs for similarity, creates
        name mapping from shorter to longer values, and returns standardized
        names.

        Args:
            inner_values: List of names to be compared and standardized.

        Returns:
            List of standardized names.
        """
        name_map: dict = defaultdict(str)

        cleaned_values = {
            value: data_cleaner.remove_titles(value) for value in inner_values
        }

        for i, value_i in enumerate(inner_values):
            clean_i = cleaned_values[value_i]
            for value_j in inner_values[i + 1 :]:  # noqa: E203
                if self._should_compare_values(value_i, value_j):
                    clean_j = cleaned_values[value_j]
                    shorter_value, longer_value = self._sort_shorter_longer(
                        clean_i, clean_j
                    )
                    name_map[shorter_value] = longer_value

        standardized_names = {
            name_map.get(cleaned_values[name], cleaned_values[name])
            for name in inner_values
        }

        return list(standardized_names)

    @staticmethod
    def _sort_shorter_longer(clean_i: str, clean_j: str) -> tuple[str, str]:
        """Get the shorter and longer of two cleaned names.

        Args:
            clean_i: First cleaned name.
            clean_j: Second cleaned name.

        Returns:
            Tuple of (shorter_name, longer_name).
        """
        if clean_i == data_cleaner.to_singular(clean_j):
            return clean_i, clean_j
        elif clean_j == data_cleaner.to_singular(clean_i):
            return clean_j, clean_i
        else:
            shorter, longer = sorted([clean_i, clean_j], key=len)
            return shorter, longer

    def _finalize_dict(self) -> dict:
        """Finalize the dictionary by building the NER dictionary.

        Returns:
            The finalized NER dictionary.
        """
        if self._category_name:
            self._set_category_dict()
        return self._build_ner_dict()

    def _process_remaining_modifications(self, line: str) -> str:
        """Process the remaining modifications to the line.

        Args:
            line (str): The line to process.

        Returns:
            str: The processed line.
        """
        if self._has_odd_parentheses(line):
            line = self._remove_parentheses(line)
        if self._has_bad_setting(line):
            line = self._replace_bad_setting()
        if self._has_narrator(line):
            line = self._narrator
        return self._remove_parantheticals_pattern(line)

    def _split_and_update_lines(
        self, index: int, split_func: Callable[[str], tuple[list[str], int]]
    ) -> None:
        """Split line at index using split function and update lines list.

        Args:
            index: Index of the line to split.
            split_func: Function to split the line.
        """
        split_lines: list[str]

        split_lines, _ = split_func(self._lines[index])
        self._lines[index : index + 1] = split_lines  # noqa: E203

    def sort(self) -> dict:
        """Clean the lines and sort into a dictionary.

        Performs operations on split strings to standardize and organize
        them before sorting into a categorized NER dictionary.

        Returns:
            Dictionary containing sorted names categorized by type.
        """
        split_conditions = [
            (self._is_list_as_str, self._split_at_commas),
            (self._needs_newline, self._add_missing_newline),
        ]

        i = 0
        while i < len(self._lines):
            line = self._lines[i].strip()
            line = self._remove_list_formatting(line)
            if self._starts_with_location(line):
                self._split_and_update_lines(i, self._split_settings_line)
                continue
            line = self._lowercase_interior_exterior(line)
            line = self._replace_inverted_setting(line)

            split: bool = False
            for condition, split_func in split_conditions:
                if condition(line):
                    self._split_and_update_lines(i, split_func)
                    split = True
                    break
            if split:  # When line is split, start iteration over at same index
                continue

            line = self._remove_leading_colon_pattern(line)
            if self._should_skip_line(line):
                self._lines.pop(i)
                continue
            line = self._process_remaining_modifications(line)

            # Remaining lines ending with a colon are category names and lines
            # following belong in a list for that category
            self._add_to_dict(line)
            i += 1

        return self._finalize_dict()
