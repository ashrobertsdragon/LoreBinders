from file_handling import FileHandler

files = FileHandler()

class Book():
    """
    A book or collection of chapters
    """

    def __init__(self, file_path):
        """
        Initializes the Book object by reading the input file and splitting it
        into chapters.
        """
        self.book = files.read_text_file(file_path)
    
    def get_chapters(self):
        """
        Returns a list of Chapter objects
        """
        self.chapters = [Chapter(number, text) for number, text in enumerate(files.split_into_chapters(self.book), start=1)]

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