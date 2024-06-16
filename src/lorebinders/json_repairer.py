import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from json_repair import repair_json

from file_handling import read_json_file


class JSONRepair:
    def _find_full_object(self, string: str, forward: bool = True) -> int:
        """
        Finds the position of the first full object of a string representation
        of a partial JSON object
        """

        balanced = 0 if forward else -1
        count = 0
        for i, char in enumerate(string):
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
            if i != 0 and count == balanced:
                return i
        return 0

    def is_valid_json(self, file_path: str) -> bool:
        "Checks to see if JSON file exists and is non-empty"

        return (
            bool(read_json_file(file_path))
            if os.path.exists(file_path)
            else False
        )

    def merge(self, first_half: str, second_half: str) -> Optional[str]:
        """
        Merges two strings of a partial JSON object

        Args:
            first_half: str - the first segment of a partial JSON object in
                string form
            second_half: str - the second segment of a partial JSON object in
                string form

        Returns either the combined string of a full JSON object or None
        """

        repair_stub = (
            f"First response:\n{first_half}\nSecond response:\n{second_half}"
        )

        first_end = self._find_full_object(first_half[::-1], forward=False)
        second_start = self._find_full_object(second_half)
        if first_end and second_start:
            first_end = len(first_half) - first_end - 1
            combined_str = (
                first_half[: first_end + 1] + ", " + second_half[second_start:]
            )

        else:
            log = f"Could not combine.\n{repair_stub}"
            logging.warning(log)
            return None

        try:
            return json.loads(combined_str)
        except json.JSONDecodeError:
            logging.error(
                f"Did not properly repair.\n{repair_stub}\n"
                f"Combined is:\n{combined_str}"
            )
            return None

    def repair(
        self, bad_string: str
    ) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
        return repair_json(bad_string, return_objects=True)

    def repair_str(self, bad_string: str) -> str:
        return repair_json(bad_string)

    def json_str_to_dict(self, json_str: str) -> dict:
        return repair_json(json_str)
