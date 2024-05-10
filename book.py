from file_handling import FileHandler
from error_handler import ErrorHandler

files = FileHandler()

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
        self.__dict__ = {key: book_dict[key] for key in book_dict.keys()}
        self.file = files.read_text_file(self.file_path)
        self.error_handler = ErrorHandler(__name__)

    def __name__(self):
        self.name = self.title

    def get_chapters(self):
        """
        Returns a list of Chapter objects
        """
        chapters = []
        for number, text in enumerate(files.split_into_chapters(self.file), start=1):
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
        self.number = number
        self.text = text