import os

from ebook2text.convert_file import convert_file  # type: ignore

from binders import Binder
from book import Book
from book_dict import BookDict
from make_pdf import create_pdf


def create_book(book_dict: BookDict) -> Book:
    return Book(book_dict)


def create_lorebinder(book: Book, ai_model) -> Binder:
    return Binder(book, ai_model)


def build_binder(lorebinder: Binder) -> None:
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


def create_txt_filename(book_dict: BookDict, book_file: str) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: str, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict) -> None:
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder = create_user_folder(author)
    file_path = os.path.join(user_folder, book_file)
    limited_metadata = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    create_txt_filename(book_dict, book_file)


def run(book_dict: BookDict) -> None:
    convert_book_file(book_dict)

    book = create_book(book_dict)
    ai_model = os.getenv("ai_model")  # Placeholder
    lorebinder = create_lorebinder(book, ai_model)
    build_binder(lorebinder)
    if book_dict.user_folder is not None:
        create_pdf(book_dict.user_folder, book_dict.title)
