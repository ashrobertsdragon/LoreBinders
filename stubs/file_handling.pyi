from _types import T as T

def read_text_file(self, file_path: str) -> str: ...
def read_json_file(self, file_path: str) -> T: ...
def write_to_file(self, content: str, file_path: str) -> None: ...
def separate_into_chapters(self, text: str) -> list: ...
def write_json_file(self, content: T, file_path: str) -> None: ...
def append_json_file(self, content: list | dict, file_path: str) -> None: ...
