import os

from binders import Binder
from book import Book
from book_dict import BookDict
from dotenv import load_dotenv
from ebook2text.convert_file import convert_file  # type: ignore
from make_pdf import create_pdf
from user_input import get_book

load_dotenv()


def create_lorebinder(book_dict: BookDict) -> None:
    book = Book(book_dict)
    lorebinder = Binder(book)

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


def create_txt_filename(book_dict, book_file) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: str, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    limited_metadata = {"title": title, "author": author}
    return limited_metadata


def main():
    book_dict = get_book()

    book_file = book_dict.book_file
    author = book_dict.author

    user_folder = create_user_folder(author)
    file_path = os.path.join(user_folder, book_file)
    limited_metadata = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    create_txt_filename(book_dict, book_file)

    create_lorebinder(book_dict, user_folder)
    create_pdf(book_dict.user_folder, book_dict.title)


if __name__ == "__main__":
    main()
