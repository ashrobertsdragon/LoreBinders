from dataclasses import dataclass


@dataclass
class BookDict:
    """Data class containing book metadata.

    Attributes:
        book_file: Path to the book file.
        title: Title of the book.
        author: Author of the book.
        narrator: Name of the narrator, if any.
        character_traits: List of character traits to search for.
        custom_categories: List of custom categories to search for.
        user_folder: Path to the user's working folder.
        txt_file: Name of the converted text file.
    """

    book_file: str
    title: str
    author: str
    narrator: str | None = None
    character_traits: list[str] | None = None
    custom_categories: list[str] | None = None
    user_folder: str | None = None
    txt_file: str | None = None

    def set_user_folder(self, user_folder: str) -> None:
        """Set the user folder path.

        Args:
            user_folder: Path to the user's working folder.
        """
        self.user_folder = user_folder

    def set_txt_file(self, txt_file: str) -> None:
        """Set the text file name.

        Args:
            txt_file: Name of the converted text file.
        """
        self.txt_file = txt_file
