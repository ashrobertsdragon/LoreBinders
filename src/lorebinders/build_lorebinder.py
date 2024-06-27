import os
from typing import Type

from ebook2text.convert_file import convert_file  # type: ignore

import make_pdf
from _types import AIProviderManager
from ai.ai_models._model_schema import AIModelRegistry
from ai.ai_models.json_file_model_handler import JSONFileProviderHandler
from binders import Binder
from book import Book
from book_dict import BookDict


def create_book(book_dict: BookDict) -> Book:
    return Book(book_dict)


def create_lorebinder(book: Book, ai_model) -> Binder:
    return Binder(book, ai_model)


def build_binder(lorebinder: Binder) -> None:
    lorebinder.build_binder()


def create_folder(folder: str, base_dir: str) -> str:
    created_path = os.path.join(base_dir, folder)
    os.makedirs(created_path, exist_ok=True)
    return created_path


def create_user(author: str) -> str:
    names = author.split(" ")
    return "_".join(names)


def create_user_folder(author: str, work_dir: str) -> str:
    user = create_user(author)
    return create_folder(user, work_dir)


def add_txt_filename(book_dict: BookDict, book_file: str) -> None:
    base, _ = os.path.splitext(book_file)
    txt_filename = f"{base}.txt"
    book_dict.txt_file = txt_filename


def convert(file_path: str, limited_metadata: dict) -> None:
    convert_file(file_path, limited_metadata)


def create_limited_metadata(book_dict: BookDict) -> dict:
    author = book_dict.author
    title = book_dict.title
    return {"title": title, "author": author}


def convert_book_file(book_dict: BookDict, work_dir: str) -> None:
    book_file = book_dict.book_file
    author = book_dict.author

    user_folder = create_user_folder(author, work_dir)
    file_path = os.path.join(user_folder, book_file)
    limited_metadata = create_limited_metadata(book_dict)
    convert(file_path, limited_metadata)
    add_txt_filename(book_dict, book_file)


def initialize_ai_model_registry(
    provider_registry: Type[AIProviderManager], *args, **kwargs
) -> AIModelRegistry:
    """
    Initializes and returns an AIModelRegistry from the provided handler.

    Args:
        provider_registry (AIProviderManager subclass): An uninitialized
        concrete subclass of the AIProviderManager abstract class.
        args: Any positional arguments that need to be passed to the provider
        class at initialization.
        kwargs: Any keyword arguments that need to be passed to the provider
        class at initialization.

    Returns:
        AIModelRegistry: A dataclass containing a list of all the provider
        classes in the data file/database.
    """
    handler = provider_registry(*args, **kwargs)
    return handler.registry


def start(book_dict: BookDict, work_base_dir: str) -> None:
    convert_book_file(book_dict, work_base_dir)

    book = create_book(book_dict)
    ai_registry = initialize_ai_model_registry(
        JSONFileProviderHandler, "json_files"
    )
    ai_models = ai_registry.get_provider("OpenAI")

    lorebinder = create_lorebinder(book, ai_models)
    build_binder(lorebinder)

    if book_dict.user_folder is not None:
        make_pdf.create_pdf(book_dict.user_folder, book_dict.title)
