import os
from typing import List, Optional

from binders import Binder
from book import Book
from dotenv import load_dotenv
from ebook2text.convert_file import convert_file  # type: ignore
from pydantic import BaseModel
from user_input import get_book

load_dotenv()


class BookDict(BaseModel):
    book_file: str
    title: str
    author: str
    narrator: Optional[str]
    character_traits: Optional[List[str]]
    custom_categories: Optional[List[str]]
    user_folder: str


def create_lorebinder(book_dict: BookDict) -> None:
    book = Book(book_dict)
    lorebinder = Binder(book)
    lorebinder.perform_ner()
    lorebinder.analyze_names()
    lorebinder.summarize()
    lorebinder.build_binder()


def create_folder(user: str) -> str:
    user_folder = os.path.join("work", user)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def create_user(author: str) -> str:
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str) -> str:
    user = create_user(author)
    return create_folder(user)


def check_file(book_dict, book_file, user_folder, metadata) -> None:
    _, ext = os.path.splitext(book_file)
    if ext != "txt":
        txt_file = convert_file(user_folder, book_file, metadata)
        book_dict[book_file] = txt_file


def main():
    book_dict = get_book()

    book_file = book_dict["book_file"]
    author = book_dict["author"]
    title = book_dict["title"]
    metadata = {"title": title, "author": author}

    user_folder = create_user_folder(author)
    check_file(book_dict, book_file, user_folder, metadata)
    create_lorebinder(book_dict, user_folder)


if __name__ == "__main__":
    main()
