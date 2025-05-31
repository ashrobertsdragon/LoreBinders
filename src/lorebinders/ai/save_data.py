from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from lorebinders._type_annotations import Book

import lorebinders.file_handling as file_handling


class MetadataNotSetError(Exception):
    """Raised when required metadata is not set."""

    pass


def get_book_by_name(book_name: str) -> Book:
    """Get a Book object by name from globals.

    Args:
        book_name: Name of the book to retrieve.

    Returns:
        The Book object.

    Raises:
        KeyError: If book is not found.
    """
    try:
        return globals()[book_name]
    except (IndexError, KeyError) as e:
        logger.exception(f"Book {book_name} not found.")
        raise KeyError(f"Book {book_name} not found.") from e


def get_file_paths(metadata_user_folder: str | None) -> dict[str, Path]:
    """Get file paths for saving data.

    Args:
        metadata_user_folder: Path to user folder, or None.

    Returns:
        Dictionary mapping file types to Path objects.

    Raises:
        MetadataNotSetError: If user_folder is not set.
    """
    if metadata_user_folder is None:
        raise MetadataNotSetError("user_folder must be set in the BookDict.")
    user_folder = Path(metadata_user_folder)
    return {
        "names_file": user_folder / "names.json",
        "analysis_file": user_folder / "analysis.json",
    }


def append_data_to_files(chapters: list, file_paths: dict) -> None:
    """Append chapter data to JSON files.

    Args:
        chapters: List of chapter objects with names and analysis.
        file_paths: Dictionary mapping file types to paths.
    """
    for chapter in chapters:
        file_handling.append_json_file(chapter.names, file_paths["names_file"])
        file_handling.append_json_file(
            chapter.analysis, file_paths["analysis_file"]
        )


def save_progress(book_name: str) -> bool:
    """Save book progress to files.

    Args:
        book_name: Name of the book to save.

    Returns:
        True if save succeeded, False otherwise.
    """
    try:
        book = get_book_by_name(book_name)
        file_paths = get_file_paths(book.metadata.user_folder)
        append_data_to_files(book.chapters, file_paths)
        return True
    except KeyError:
        logger.error(f"Failed to save data for book: {book_name}")
        return False
