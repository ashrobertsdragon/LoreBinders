from file_handling import FileManager
from binders import Binder

class Book():
    """
    A book or collection of chapters

    Attributes:
        book_dict (dict): A dictionary containing the book data.
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
                    cateogiries for the AI to search for. Defaults to None,
                    meaning only Characters and Settings are used.
        name (str): The name of the Book instance. The title is assigned to it.
        file (str): The content of the input file.
        chapters (list): A list of Chapter objects representing the chapters
            in the book.

    Methods:
        _build_chapters: Builds the list of Chapter objects from the input file.
        add_binder: Adds a Binder dictionary to the Book object.
        update_binder: Updates the Binder dictionary in the Book object.
        get_chapters: Returns the list of Chapter objects.
        get_binder: Returns the Binder dictionary.
    """

    def __init__(self, book_dict: dict, file_manager: FileManager, binder: Binder):
        """
        Initializes the Book object by reading the input file and splitting it
        into chapters.
        """
        self.book_dict = book_dict
        for key, value in book_dict.items():
            setattr(self, key, value)

        self.name = self.title
        self.file_manager = file_manager
        self.binder = binder

        self.file: str = self.file_handler.read_text_file(self.file_path)
        self.chapters: list = self._build_chapters()

    def _build_chapters(self) -> None:
        """
        Returns a list of Chapter objects
        """
        chapters: list = []
        for number, text in enumerate(self.file_manager.split_into_chapters(self.file), start=1):
            chapters.append(Chapter(number, text))
        self._chapters = chapters
    
    def set_binder_type(self, binder_class: Binder) -> None:
        """
        Allows changing the binder dynamically.

        This method expects a Binder subclass.
        """
        if not issubclass(binder_class, Binder):
            raise TypeError("Binder must be a subclass of the Binder class")
        self.binder = binder_class(self, __name__)
    
    def add_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        self.binder.add_binder(binder)
    
    def update_binder(self, binder: dict) -> None:
        if not isinstance(binder, dict):
            raise TypeError("Binder must be a dictionary")
        if self.get_binder() != binder:
            self.add_binder(binder)

    @property
    def get_chapters(self) -> list:
        return self._chapters

    @property
    def get_binder(self) -> dict:
        return self.binder


class Chapter():
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

    def add_names(self, names: dict) -> None:
        """
        Adds a dictionary of names to the Chapter object.

        Args:
            names (dict): A dictionary of names for each category in the
                Chapter.
        """
        if not isinstance(names, list):
            raise TypeError("Names must be a dictionary")
        self.names: list = names
    
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
