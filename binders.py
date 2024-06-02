from typing import Optional, Union

from _managers import FileManager
from _types import Book


class Binder:
    """
    Base class for all book analysis binders.
    """

    def __init__(self, book: Book) -> None:
        self.book = book
        self.binder_type = __name__.lower()
        self._book_name: Optional[str] = None
        self._file_manager: Optional[FileManager] = None
        self._temp_file: Optional[str] = None

    @property
    def book_name(self) -> str:
        if self._book_name is None:
            self._book_name = self.book.name
        return self._book_name

    @property
    def file_manager(self):
        if self._file_manager is None:
            self._file_manager = self.book.file_manager
        return self._file_manager

    @property
    def get_binder_tempfile(self) -> str:
        if self._temp_file is None:
            self._temp_file = f"{self.book_name}-{self.binder_type}.json"
        return self._temp_file

    def add_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        self._binder = binder
        self.file_manager.write_json_file(self._binder, self._temp_file)

    def update_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        if self._binder != binder:
            self.add_binder(binder)

    def get_binder_json(self) -> Union[dict, list, str]:
        return self.file_manager.read_json_file(self._temp_file)

    @property
    def get_binder(self) -> dict:
        return self._binder


class LoreBinder(Binder):
    """
    LoreBinder handles lore analysis for the book.
    """

    pass
