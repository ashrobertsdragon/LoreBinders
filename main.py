import os

from dotenv import load_dotenv
from ebook2text.convert_file import convert_file  # type: ignore
from email_handler.send_email import EmailHandler

from _types import Binder, ErrorManager
from attributes import NameAnalyzer, NameExtractor, NameSummarizer
from binders import LoreBinder
from book import Book
from data_cleaner import clean_lorebinders
from error_handler import ErrorHandler
from file_handling import FileHandler
from make_pdf import create_pdf
from user_input import get_book

load_dotenv()
email_handler = EmailHandler()
file_handler = FileHandler()


def extract_names(
    book: Book, binder: Binder, error_handler: ErrorManager
) -> None:
    extractor = NameExtractor(book, binder, error_handler)
    extractor.extract_names()


def analyze_names(
    book: Book, binder: Binder, error_handler: ErrorManager
) -> None:
    analyzer = NameAnalyzer(book, error_handler)
    analyzer.analyze_names()


def summarize_names(
    book: Book, binder: Binder, error_handler: ErrorManager
) -> None:
    summarizer = NameSummarizer(book, error_handler)
    summarizer.sumarize_names()


def build_lorebinder(book_dict: dict) -> dict:
    book = Book(
        book_dict,
        file_manager=file_handler,
    )
    binder = LoreBinder(book)
    error_handler = ErrorHandler(book, email_handler)

    extract_names(book, binder, error_handler)
    analyze_names(book, binder, error_handler)
    summarize_names(book, binder, error_handler)
    return book.get_binder


def create_lorebinder(book_dict: dict, user_folder: str):
    lorebinder_dict = build_lorebinder(book_dict)
    cleaned_lorebinder = clean_lorebinders(
        lorebinder_dict, book_dict["narrator"]
    )
    file_handler.write_json_file(cleaned_lorebinder, user_folder)


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


def make_pdf(user_folder: str, title: str) -> None:
    create_pdf(user_folder, title)


def main():
    book_dict = get_book()

    book_file = book_dict["book_file"]
    author = book_dict["author"]
    title = book_dict["title"]
    metadata = {"title": title, "author": author}

    user_folder = create_user_folder(author)
    check_file(book_dict, book_file, user_folder, metadata)
    create_lorebinder(book_dict, user_folder)
    make_pdf(user_folder, title)


if __name__ == "__main__":
    main()
