from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ebook2text.convert_file import convert_file  # type: ignore

if TYPE_CHECKING:
    from lorebinders._type_annotations import BookDict


def create_folder(folder: str, base_dir: str) -> Path:
    created_path = Path(base_dir, folder)
    created_path.mkdir(parents=True, exist_ok=True)
    return created_path


def create_user(author: str) -> str:
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str, work_dir: str) -> Path:
    user = create_user(author)
    return create_folder(user, work_dir)


def add_txt_filename(book_dict: BookDict, book_file: str) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: Path, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict, work_dir: str) -> None:
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder: Path = create_user_folder(author, work_dir)
    file_path: Path = Path(user_folder, book_file)
    limited_metadata: dict = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    add_txt_filename(book_dict, book_file)
