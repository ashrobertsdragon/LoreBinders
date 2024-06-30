from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._types import BookDict
from .file_handling import read_text_file, separate_into_chapters


class Book:
    """
    A book or collection of chapters

    Attributes:
        _metadata (dict): A dictionary containing the book data.
            contains:
                title (str): The book's title.
                author (str): The book's author.
                book_file (str): The path to the input file.
                narrator (Optional str): The name of the book's narrator, if
                    the book is written in the first person, otherwise is None.
                character_attributes_list (Optional list): A list of user
                    inputted attributes for the character category for the AI
                    to search for. Defaults to None, meaning only preselected
                    attributes are used.
                other_categories_list (Optional list): A list of user inputted
                    categories for the AI to search for. Defaults to None,
                    meaning only Characters and Settings are used.
        name (str): The name of the Book instance. The title is assigned to it.
        file (str): The content of the input file.
        chapters (list): A list of Chapter objects representing the chapters
            in the book.

    Methods:
        _build_chapters: Builds list of Chapter objects from the input file.
        add_binder: Adds a Binder dictionary to the Book object.
        update_binder: Updates the Binder dictionary in the Book object.
        get_chapters: Returns the list of Chapter objects.
        get_binder: Returns the Binder dictionary.
    """

    def __init__(self, book_dict: BookDict):
        """
        Initializes the Book object by reading the input file and splitting it
        into chapters.
        """
        self.metadata = book_dict

        self.title: str = self.metadata.title
        self.author: str = self.metadata.author
        self._book_file: str = self.metadata.book_file
        self.narrator: str | None = self.metadata.narrator
        self.character_attributes: list[str] | None = (
            self.metadata.character_traits
        )
        self.custom_categories: list[str] | None = (
            self.metadata.custom_categories
        )

        self.name = self.title

        self.file = read_text_file(self._book_file)
        self._build_chapters()

    def _build_chapters(self) -> list:
        """
        Returns a list of Chapter objects
        """
        chapters: list[Chapter] = [
            Chapter(number, text)
            for number, text in enumerate(
                separate_into_chapters(self.file), start=1
            )
        ]
        self._chapters = chapters
        return self._chapters

    def add_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        self._binder = binder

    def update_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("binder data must be a dictionary")
        if self._binder != binder:
            self.add_binder(binder)

    @property
    def chapters(self) -> list:
        return self._chapters

    @property
    def binder(self) -> dict:
        return self._binder


class Chapter:
    """
    Represents a single chapter.

    Attributes:
        number (int): The number of the chapter.
        text (str): The text of the chapter.
        names (list): A list of names associated with the chapter.
        analysis (dict): An analysis dictionary associated with the chapter.

    Methods:
        add_names: Adds a dictionary of names to the Chapter object.
        add_analysis: Adds an analysis dictionary to the Chapter object.
    """

    def __init__(self, number: int, text: str) -> None:
        """
        Initializes the Chapter object with the chapter text and number.
        """
        self.number: int = number
        self.text: str = text

    def add_analysis(self, analysis: dict) -> None:
        """
        Adds an analysis dictionary to the Chapter object.

        Args:
            analysis (dict): The dictionary of the analysis from the names
                found in the chapter.
        """
        if not isinstance(analysis, dict):
            raise TypeError("Analysis must be a dictionary")
        self.analysis: dict = analysis

    def add_names(self, names: dict) -> None:
        """
        Adds an analysis dictionary to the Chapter object.

        Args:
            Names (dict): The dictionary of names found in the chapter.
        """
        if not isinstance(names, dict):
            raise TypeError("Names must be a dictionary")
        self.names: dict = names
