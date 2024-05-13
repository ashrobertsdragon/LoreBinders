from file_handling import FileHandler
from error_handler import ErrorHandler



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

        self.file = self.file_handler.read_text_file(self.file_path)
        self.chapters = self.get_chapters()

    def __name__(self):
        self.name = self.title

    def get_chapters(self):
        """
        Returns a list of Chapter objects
        """
        chapters: list = []
        for number, text in enumerate(self.file_handler.split_into_chapters(self.file), start=1):
            chapters.append(Chapter(number, text))
        self.chapters = chapters
        return chapters

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