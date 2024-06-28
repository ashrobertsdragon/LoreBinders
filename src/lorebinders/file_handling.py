from __future__ import annotations

import json
import os
import pathlib
import re

from ._types import T


def read_text_file(file_path: str) -> str:
    "Opens and reads text file"
    return pathlib.Path(file_path).read_text()


def read_json_file(file_path: str) -> T:  # type: ignore
    "Opens and reads JSON file"
    with open(file_path) as f:
        read_file = json.load(f)
    return read_file


def write_to_file(content: str, file_path: str) -> None:
    "Appends content to text file on new line"

    with open(file_path, "a") as f:
        f.write(content + "\n")


def separate_into_chapters(text: str) -> list:
    "Splits string at dimeter of three asterisks"

    return re.split(r"\s*\*\*\s*", text)


def write_json_file(content: list | dict, file_path: str) -> None:
    "Writes JSON file"

    with open(file_path, "w") as f:
        json.dump(content, f, indent=2)


def append_json_file(content: list | dict, file_path: str) -> None:
    "Reads JSON file, and adds content to datatype before overwriting"

    read_file: list | dict = {} if isinstance(content, dict) else []
    if os.path.exists(file_path):
        read_file = read_json_file(file_path)
        if isinstance(content, list) and not isinstance(read_file, list):
            raise TypeError(f"Expected list, got {type(read_file)}")
        if isinstance(content, dict) and not isinstance(read_file, dict):
            raise TypeError(f"Expected dict, got {type(read_file)}")

    if isinstance(read_file, list) and isinstance(content, list):
        read_file.extend(content)
    elif isinstance(read_file, dict) and isinstance(content, dict):
        read_file.update(content)
    else:
        raise TypeError("Types of read_file and content don't match")
    write_json_file(read_file, file_path)
