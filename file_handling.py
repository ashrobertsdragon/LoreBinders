import json
import os
import re
from typing import Union

from _managers import FileManager
from _types import T


class FileHandler(FileManager):
    """
    Methods for reading, writing, and other I/O functions
    """

    def read_text_file(self, file_path: str) -> str:
        "Opens and reads text file"
        with open(file_path) as f:
            read_file = f.read()
        return read_file

    def read_json_file(self, file_path: str) -> T:
        "Opens and reads JSON file"
        with open(file_path) as f:
            read_file = json.load(f)
        return read_file

    def write_to_file(self, content: str, file_path: str) -> None:
        "Appends content to text file on new line"

        with open(file_path, "a") as f:
            f.write(content + "\n")

    def separate_into_chapters(self, text: str) -> list:
        "Splits string at delimeter of three asterisks"

        return re.split(r"\s*\*\*\s*", text)

    def write_json_file(self, content: T, file_path: str) -> None:
        "Writes JSON file"

        with open(file_path, "w") as f:
            json.dump(content, f, indent=2)

    def append_json_file(
        self, content: Union[list, dict], file_path: str
    ) -> None:
        "Reads JSON file, and adds content to datatype before overwriting"

        if os.path.exists(file_path):
            read_file = self.read_json_file(file_path)
        else:
            read_file = {} if isinstance(content, dict) else []
        if isinstance(read_file, list):
            read_file.append(content)
        elif isinstance(read_file, dict):
            read_file.update(content)
        self.write_json_file(read_file, file_path)
