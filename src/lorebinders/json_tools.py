from __future__ import annotations

import os

from json_repair import repair_json
from loguru import logger

import lorebinders.file_handling as file_handling


def is_valid_json_file(file_path: str) -> bool:
    "Checks to see if JSON file exists and is non-empty"

    return (
        bool(file_handling.read_json_file(file_path))
        if os.path.exists(file_path)
        else False
    )


def repair_json_str(bad_string: str) -> str:
    """
    Repairs any syntax errors in a given JSON string.

    Args:
        bad_string (str): The JSON string with syntax errors to be
            repaired.

    Returns:
        str: A valid JSON string after repairing any syntax errors.

    """
    return repair_json(bad_string)


def json_str_to_dict(json_str: str) -> dict:
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

    def _set_halves(self, first_half: str, second_half: str) -> None:
        """
        Sets the end indices of the first and second JSON objects in the
        first and second segments, respectively.
        """
        self.first_half = first_half
        self.second_half = second_half

        self.repair_stub = (
            f"First response:\n{first_half}\nSecond response:\n{second_half}"
        )

    def find_ends(self) -> tuple[int, int]:
        """
        Finds the end index of the first JSON object in the first segment and
        the start index of the second JSON object in the second segment.
        """
        first_end = self._find_full_object(self.first_half, forward=False)
        second_start = self._find_full_object(self.second_half)
        return first_end, second_start

    @staticmethod
    def _find_full_object(string: str, forward: bool = True) -> int:
        """
        Finds the position of the first full object of a string representation
        of a partial JSON object.
        """

        balanced: int = 0 if forward else -1
        count: int = 0
        last_balanced_position: int = 0

        directional_string: str = string if forward else string[::-1]
        for i, char in enumerate(directional_string):
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
            if count == balanced:
                last_balanced_position = i

        if count != 0:
            return 0

        return (
            last_balanced_position if forward else last_balanced_position + 1
        )

    def _merge_halves(self, first_end: int, second_start: int) -> str:
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

        if first_end and second_start:
            return (
                self.first_half[:first_end]
                + ", "
                + self.second_half[second_start:]
            )
        log = f"Could not combine.\n{self.repair_stub}"
        logger.warning(log)
        return ""

    def merge(self, first_half: str, second_half: str) -> str:
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
        self._set_halves(first_half, second_half)
        first_end, second_start = self.find_ends()
        return self._merge_halves(first_end, second_start)
