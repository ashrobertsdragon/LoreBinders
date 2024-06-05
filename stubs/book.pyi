from _typeshed import Incomplete

from _managers import FileManager as FileManager

class Book:
    title: Incomplete
    author: Incomplete
    narrator: Incomplete
    character_attributes: Incomplete
    other_attributes: Incomplete
    name: Incomplete
    file_manager: Incomplete
    file: Incomplete
    chapters: Incomplete
    def __init__(
        self, _book_dict: dict, *, file_manager: FileManager
    ) -> None: ...
    def add_binder(self, binder: dict) -> None: ...
    def update_binder(self, binder: dict) -> None: ...
    @property
    def get_chapters(self) -> list: ...
    @property
    def get_binder(self) -> dict: ...

class Chapter:
    number: Incomplete
    text: Incomplete
    def __init__(self, number: int, text: str) -> None: ...
    analysis: Incomplete
    def add_analysis(self, analysis: dict) -> None: ...
    names: Incomplete
    def add_names(self, names: dict) -> None: ...
