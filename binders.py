from abc import ABC, abstractmethod

from _types import Book
class Binder(ABC):
    """
    Base class for all book analysis binders.
    """

    def __init__(self, book: Book, temp_file: str):
        self.book = book
        self.file_manager = book.file_manager
    @abstractmethod
    def add_binder(self, data):
        raise NotImplementedError("Subclasses must implement add_binder")
    @abstractmethod
    def update_binder(self, data):
        raise NotImplementedError("Subclasses must implement update_binder")
    @property @abstractmethod
    def get_binder(self):
        raise NotImplementedError("Subclasses must implement get_binder")
    @property @abstractmethod
    def get_binder_tempfile(self):
        raise NotImplementedError("Subclasses must implement get_binder")

class LoreBinder(Binder):
    """
    LoreBinder handles lore analysis for the book.
    """
    def __init__(self, book_name: str):
        super().__init__()
        self.temp_file = f"{book_name}-lorebinder.json"

    def add_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        self.binder = binder
        self.file_manager.write_json_file(binder, self._temp_file)

    def update_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        if self.binder != binder:
            self.add_binder(binder)

    def get_binder_json(self) -> any:
        return self.file_manager.read_json_file(self.temp_file)
    @property
    def get_binder(self) -> dict:
        return self._binder
    
    @property
    def get_binder_tempfile_path(self) -> str:
        return self._temp_file
