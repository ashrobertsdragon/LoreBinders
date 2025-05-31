from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ebook2text.convert_file import convert_file  # type: ignore

if TYPE_CHECKING:
    from lorebinders._type_annotations import BookDict


def create_folder(folder: str, base_dir: str) -> Path:
    """Create a folder within a base directory.

    Args:
        folder: Name of the folder to create.
        base_dir: Base directory path.

    Returns:
        Path object for the created folder.
    """
    created_path = Path(base_dir, folder)
    created_path.mkdir(parents=True, exist_ok=True)
    return created_path


def create_user(author: str) -> str:
    """Create a user identifier from author name.

    Args:
        author: Full name of the author.

    Returns:
        Author name with spaces replaced by underscores.
    """
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str, work_dir: str) -> Path:
    """Create a user-specific folder for the author.

    Args:
        author: Full name of the author.
        work_dir: Working directory path.

    Returns:
        Path object for the created user folder.
    """
    user = create_user(author)
    return create_folder(user, work_dir)


def add_txt_filename(book_dict: BookDict, book_file: str) -> None:
    """Add the converted text filename to the book dictionary.

    Args:
        book_dict: Book metadata object to update.
        book_file: Original book file path.
    """
    txt_filename: str = Path(book_file).with_suffix(".txt").name
    book_dict.txt_file = txt_filename


def convert(file_path: Path, limited_metadata: dict) -> None:
    """Convert an ebook file to text format.

    Args:
        file_path: Path to the ebook file.
        limited_metadata: Metadata dictionary for conversion.
    """
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    """Create a limited metadata dictionary for conversion.

    Args:
        book_dict: Book metadata object.

    Returns:
        Dictionary containing title and author information.
    """
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict, work_dir: str) -> None:
    """Convert a book file to text format in the user's working directory.

    Args:
        book_dict: Book metadata object containing file information.
        work_dir: Working directory for output files.
    """
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder: Path = create_user_folder(author, work_dir)
    file_path: Path = Path(user_folder, book_file)
    limited_metadata: dict = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    add_txt_filename(book_dict, book_file)
