from file_handling import FileHandler
from error_handler import ErrorHandler
from make_pdf import create_pdf


class Book():
    """
    A book or collection of chapters
    """

    def __init__(self, book_dict):
        """
        Initializes the Book object by reading the input file and splitting it
        into chapters.
        """
        self.book_dict = book_dict
        for key, value in book_dict.items():
            setattr(self, key, value)

        self.error_handler = ErrorHandler(__name__)
        self.file_handler = FileHandler()

        self.lorebinder_temp = f"{__name__}-lorebinder.json"

        self.file = self.file_handler.read_text_file(self.file_path)
        self.chapters = self._build_chapters()

    def __name__(self):
        self.name = self.title

    def _build_chapters(self):
        """
        Returns a list of Chapter objects
        """
        chapters: list = []
        for number, text in enumerate(self.file_handler.split_into_chapters(self.file), start=1):
            chapters.append(Chapter(number, text))
        self.chapters = chapters
        return chapters
    
    def add_lorebinder(self, lorebinder: dict) -> None:
        if not isinstance(lorebinder, dict):
            raise TypeError("LoreBinder must be a dictionary")
        self.lorebinder = lorebinder
        self.file_handler.write_json_file(lorebinder, self.lorebinder_temp)

    def update_lorebinder(self, lorebinder: dict) -> None:
        if not isinstance(lorebinder, dict):
            raise TypeError("LoreBinder must be a dictionary")
        if self.lorebinder != lorebinder:
            self.file_handler.write_json_file(lorebinder, self.lorebinder_temp)
        self.lorebinder = lorebinder

    def create_pdf(self) -> None:
        create_pdf(self.folder_name, __name__)

    @property
    def get_chapters(self) -> list:
        return self.chapters

    @property
    def get_lorebinder(self) -> dict:
        return self.lorebinder


class Chapter():
    """
    Represents a single chapter.
    """
    def __init__(self, number: int, text: str) -> None:
        """
        Initializes the Chapter object with the chapter text and number.
        """
        self.number: int = number
        self.text: str = text

    def add_names(self, names: list) -> None:
        self.names: list = names
    
    def add_analysis(self, analysis: dict) -> None:
        self.summary: dict = analysis