import os

from convert_file import convert_file
from dotenv import load_dotenv

from attributes import NameExtractor, NameAnalyzer, NameSummarizer
from binders import LoreBinder
from book import Book
from data_cleaner import clean_lorebinders
from error_handler import ErrorHandler
from file_handling import FileHandler
from make_pdf import create_pdf
from user_input import get_book


load_dotenv()
error_handler = ErrorHandler()
file_handler = FileHandler()
lorebinder = LoreBinder()

def extract_names(book) -> None:
    extractor = NameExtractor(book)
    extractor.extract_names()
    
def analyze_names(book) -> None:
    analyzer = NameAnalyzer(book)
    analyzer.analyze_names()

def summarize_names(book) -> None:
    summarizer = NameSummarizer(book)
    summarizer.sumarize_names()

def build_lorebinder(book_dict: dict) -> dict:
    book = Book(
        book_dict,
        binder=lorebinder,
        error_manager=error_handler,
        file_manager=file_handler
    )

    extract_names(book)
    analyze_names(book)
    summarize_names(book)
    return book.get_binder()

def create_lorebinder(book_dict: dict, user_folder: str):
    lorebinder_dict = create_lorebinder(book_dict)
    cleaned_lorebinder = clean_lorebinders(lorebinder_dict, book_dict["narrator"])
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
