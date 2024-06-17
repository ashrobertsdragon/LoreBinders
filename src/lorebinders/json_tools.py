import json
import logging
import os

from json_repair import repair_json

from file_handling import read_json_file


def is_valid_json_file(file_path: str) -> bool:
    "Checks to see if JSON file exists and is non-empty"

    return (
        bool(read_json_file(file_path)) if os.path.exists(file_path) else False
    )


class MergeJSON:
    """
    A class to merge two partial JSON objects and validate the combined
    JSON string.

    Attributes:
        first_half (str): The first segment of a partial JSON object in string
            form.
        second_half (str): The second segment of a partial JSON object in
            string form.
        repair_stub (str): A formatted string containing the first and second
            response halves.
        first_end (int): The index of the end of the first JSON object in the
            first segment.
        second_start (int): The index of the start of the second JSON object
            in the second segment.

    Methods:
        merge:
            Merges the two partial JSON object segments and returns the
                combined string.

        is_valid:
            Validates the combined JSON string by attempting to load it as
                JSON.

    Warnings:
        If the merge operation fails, a warning is logged with details of the
            failure.
        If the validation fails, an error is logged with details of the
            failure.
    """

    def __init__(self, first_half: str, second_half: str):
        self.first_half = first_half
        self.second_half = second_half

        self.repair_stub = (
            f"First response:\n{first_half}\nSecond response:\n{second_half}"
        )
        self.first_end: int = 0
        self.second_start: int = 0

    def _find_ends(self) -> None:
        """
        Finds the end index of the first JSON object in the first segment and
        the start index of the second JSON object in the second segment.
        """
        self.first_end: int = self._find_full_object(
            self.first_half[::-1], forward=False
        )
        self.second_start: int = self._find_full_object(self.second_half)

    def _find_full_object(self, string: str, forward: bool = True) -> int:
        """
        Finds the position of the first full object of a string representation
        of a partial JSON object.
        """

        balanced = 0 if forward else -1
        count = 0
        for i, char in enumerate(string):
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
            return i if i != 0 and count == balanced else 0

    def merge(self) -> str:
        """
        Merges two strings of a partial JSON object

        Args:
            first_half: str - the first segment of a partial JSON object in
                string form
            second_half: str - the second segment of a partial JSON object in
                string form

        Returns either the combined string of a full JSON object or empty
            string.
        """

        if self.first_end and self.second_start:
            self.first_end = len(self.first_half) - self.first_end - 1
            return (
                self.first_half[: self.first_end + 1]
                + ", "
                + self.second_half[self.second_start :]
            )

        else:
            log = f"Could not combine.\n{self.repair_stub}"
            logging.warning(log)
            return ""

    def is_valid_json_str(self, combined_str: str) -> bool:
        """
        Validates the combined JSON string by attempting to load it as JSON.

        Args:
            combined_str (str): The combined string of two partial JSON
                objects.

        Returns:
            bool: True if the combined string is valid JSON, False otherwise.
        """
        try:
            json.loads(combined_str)
            return True
        except json.JSONDecodeError:
            logging.error(
                f"Did not properly repair.\n{self.repair_stub}\n"
                f"Combined is:\n{combined_str}"
            )
            return False


class RepairJSON:
    """
    A class for repairing JSON strings with syntax errors and converting JSON
    strings to Python dictionaries.

    Methods:
        repair_str: Repairs any syntax errors in a given JSON string.
        json_str_to_dict: Converts a JSON string to a Python dictionary by
            repairing any syntax errors in the JSON string.
    """

    def repair_str(self, bad_string: str) -> str:
        """
        Repairs any syntax errors in a given JSON string.

        Args:
            bad_string (str): The JSON string with syntax errors to be
                repaired.

        Returns:
            str: A valid JSON string after repairing any syntax errors.

        """
        return repair_json(bad_string)

    def json_str_to_dict(self, json_str: str) -> dict:
        """
        Converts a JSON string to a Python dictionary by repairing any syntax
        errors in the JSON string.

        Args:
            json_str (str): The JSON string to be converted to a dictionary.

        Returns:
            dict: A Python dictionary representing the JSON data after
                repairing any syntax errors.

        """
        return repair_json(json_str)
