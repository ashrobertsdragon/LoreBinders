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


# Merge JSON objects
def build_repair_stub(
    first_part: str, second_part: str, first_end: int, second_start: int
) -> str:
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
    repair_stub = []
    for index, part in zip(
        (first_end, second_start), (first_part, second_part)
    ):
        if index == 0:
            stub = f"{part}\nhas no complete object"
        else:
            stub = f"{part}\ncomplete object at index {index}"
        repair_stub.append(stub)
    return "\n".join(repair_stub)


def log_merge_warning(
    first_part: str, second_part: str, first_end: int, second_start: int
) -> None:
    """
    Logs a warning with details of the merge operation.

    Args:
        first_part (str): The first partial JSON object.
        second_part (str): The second partial JSON object.

    Returns:
        None
    """

    repair_stub = build_repair_stub(
        first_part, second_part, first_end, second_start
    )
    log = f"Could not combine.\n{repair_stub}"
    logger.warning(log)


def find_ends(first_part: str, second_part: str) -> tuple[int, int]:
    """
    Finds the end index of the first JSON object in the first segment and
    the start index of the second JSON object in the second segment.

    Args:
        first_part (str): The first partial JSON object.
        second_part (str): The second partial JSON object.

    Returns:
        tuple[int, int]: The end index of the first JSON object in the first
            segment and the start index of the second JSON object in the
            second segment.
    """
    first_end = find_full_object(first_part, forward=False)
    second_start = find_full_object(second_part)
    return first_end, second_start


def find_full_object(string: str, forward: bool = True) -> int:
    """
    Finds the position of the first full object of a string representation
    of a partial JSON object.

    Iterates from the 'broken' end of a partial JSON object and returns the
    position of the end of the first complete object in the string from the
    direction specified. If no complete object is found, returns 0.
    If traversing the string in the reverse direction (forward=False), the
    position is still the RIGHT end of the first complete object.

    Args:
        string (str): The string representation of a partial JSON object.
        forward (bool, optional): Flag to trigger the traversing direction.
            True is left to right. False is right to left. Defaults to True.

    Returns:
        int: The position of the end of the first complete object in the
            string from the direction specified.
    """

    count: int = 0
    directional_string: str = string if forward else string[::-1]

    for i, char in enumerate(directional_string):
        if char == "{":
            count += 1
        elif char == "}":
            count -= 1
        if count == 0:
            # return the position from the end being iterated from
            return i if forward else len(string) - i - 1

    return 0


def merge_halves(
    first_part: str, second_part: str, first_end: int, second_start: int
) -> str:
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
    if first_end and second_start:
        return f"{first_part[:first_end]},{second_part[second_start:]}"
    log_merge_warning(first_part, second_part, first_end, second_start)
    return ""


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

    first_end, second_start = find_ends(first_part, second_part)
    return merge_halves(first_part, second_part, first_end, second_start)
