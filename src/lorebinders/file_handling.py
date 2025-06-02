from __future__ import annotations

import json
import re
from pathlib import Path

from lorebinders._types import T


def read_text_file(file_path: Path) -> str:
    """Open and read text file.

    Args:
        file_path: Path to the text file.

    Returns:
        Content of the text file.
    """
    return file_path.read_text()


def read_json_file(file_path: Path) -> T:  # type: ignore
    """Open and read JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON content.
    """
    with file_path.open() as f:
        read_file = json.load(f)
    return read_file


def write_to_file(content: str, file_path: Path) -> None:
    """Append content to text file on new line.

    Args:
        content: Content to append.
        file_path: Path to the text file.
    """
    with file_path.open("a") as f:
        f.write(content + "\n")


def separate_into_chapters(text: str) -> list:
    """Splits string at delimiter of three asterisks.

    Args:
        text: The text to split into chapters.

    Returns:
        List of chapter strings.
    """
    return re.split(r"\s*\*\*\*\s*", text)


def write_json_file(content: list | dict, file_path: Path) -> None:
    """Writes JSON file.

    Args:
        content: Data to write to the JSON file.
        file_path: Path to the JSON file.
    """
    with file_path.open("w") as f:
        json.dump(content, f, indent=2)


def append_json_file(content: list | dict, file_path: Path) -> None:
    """Reads JSON file, and adds content to datatype before overwriting.

    Args:
        content: Data to append to the JSON file.
        file_path: Path to the JSON file.

    Raises:
        TypeError: If content type doesn't match existing file type.
    """
    read_file: list | dict = {} if isinstance(content, dict) else []
    if file_path.exists():
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
