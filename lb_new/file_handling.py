import json
import re

class FileHandler():
    """
    Methods for reading, writing, and other I/O functions
    """
    def read_text_file(file_path: str) -> str:
        "Opens and reads text file"
        with open(file_path, "r") as f:
            read_file = f.read()
        return read_file

    def read_json_file(file_path: str) -> str:
        "Opens and reads JSON file"
        with open(file_path, "r") as f:
            read_file = json.load(f)
        return read_file

    def write_to_file(content: any, file_path: str) -> None:
        "Appends content to text file on new line"

        with open(file_path, "a") as f:
            f.write(content + "\n")

    def separate_into_chapters(text: str) -> list:
        "Splits string at delimeter of three asterisks"

        return re.split("\s*\*\*\s*", text)

    def write_json_file(content: any, file_path: str) -> None:
        "Writes JSON file"

        with open(file_path, "w") as f:
            json.dump(content, f, indent=2)