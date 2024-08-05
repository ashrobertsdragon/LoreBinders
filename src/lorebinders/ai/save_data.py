from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from lorebinders._type_annotations import Book, BookDict

import lorebinders.file_handling as file_handling


def get_book_by_name(book_name: str) -> Book:
    try:
        title = book_name.split("'")[1]
        return globals()[title]
    except (IndexError, KeyError) as e:
        logger.exception(f"Book {book_name} not found.")
        raise KeyError(f"Book {book_name} not found.") from e


def get_file_paths(metadata: BookDict) -> dict[str, Path]:
    user_folder = Path(metadata.user_folder or "")
    return {
        "names_file": user_folder / "names.json",
        "analysis_file": user_folder / "analysis.json",
    }


def append_data_to_files(chapters, file_paths: dict) -> None:
    for chapter in chapters:
        file_handling.append_json_file(chapter.names, file_paths["names_file"])
        file_handling.append_json_file(
            chapter.analysis, file_paths["analysis_file"]
        )


def save_progress(book_name: str) -> bool:
    try:
        book = get_book_by_name(book_name)
        file_paths = get_file_paths(book.metadata)
        append_data_to_files(book.chapters, file_paths)
        return True
    except KeyError:
        logger.error(f"Failed to save data for book: {book_name}")
        return False
