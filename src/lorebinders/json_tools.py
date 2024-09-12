from __future__ import annotations

import os
from typing import cast

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
    return cast(str, repair_json(bad_string))


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
    return cast(dict, repair_json(json_str))


# Merge JSON objects
def build_repair_stub(first_part: str, second_part: str) -> str:
    """
    Builds a string containing details of the merge operation.

    Args:
        first_part (str): The first potential partial JSON object.
        second_part (str): The second potential partial JSON object.
        first_end (int): The end index of the first JSON object in the first
            segment, if any.
        second_start (int): The start index of the second JSON object in the
            second segment, if any.

    Returns:
        str: A string containing details of the merge operation.
    """
    first_part = f"First part: {first_part}\nhas no complete object"
    second_part = f"Second part: {second_part}"
    repair_stub = [first_part, second_part]

    return "\n".join(repair_stub)


def log_merge_warning(first_part: str, second_part: str) -> None:
    """
    Logs a warning with details of the merge operation.

    Args:
        first_part (str): The first partial JSON object.
        second_part (str): The second partial JSON object.

    Returns:
        None
    """

    repair_stub = build_repair_stub(first_part, second_part)
    log = f"Could not combine.\n{repair_stub}"
    logger.warning(log)


def find_last_full_object(string: str) -> int:
    """
    Finds the position of the last full object of a string representation
    of a partial JSON object.

    Iterates from the beginning of a partial JSON object and returns the
    position of the end of the last complete object in the string. If no
    complete object is found, returns 0.

    Args:
        string (str): The string representation of a partial JSON object.

    Returns:
        int: The position of the end of the last complete object.
    """
    last_balanced_location: int = 0
    count: int = 0
    for i, char in enumerate(string[1:]):
        if char == "{":
            count += 1
        elif char == "}":
            count -= 1
        if count == 0 and char in "{}":
            last_balanced_location = i

    return last_balanced_location + 1 if last_balanced_location > 0 else 0


def merge_json(first_part: str, second_part: str) -> str:
    """
    Merges two strings of a partial JSON object

    Args:
        first_part: str - the first segment of a partial JSON object in
            string form
        second_part: str - the second segment of a partial JSON object in
            string form

    Returns either the combined string of a full JSON object or empty
        string.
    """

    if first_end := find_last_full_object(first_part):
        return f"{first_part[: first_end + 1]},{second_part.lstrip('{')}"
    log_merge_warning(first_part, second_part)
    return ""
