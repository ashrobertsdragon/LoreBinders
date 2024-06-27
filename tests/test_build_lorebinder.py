import os
from unittest.mock import MagicMock, patch

import pytest

from lorebinders._types import Book
from lorebinders.build_lorebinder import (
    convert,
    convert_book_file,
    create_book,
    create_folder,
    create_limited_metadata,
    create_lorebinder,
    add_txt_filename,
    create_user,
    create_user_folder,
)


def test_create_folder():
    user = "test_user"
    expected_folder = os.path.join("work", user)

    assert os.path.exists(expected_folder) == False
    assert create_folder(user) == expected_folder
    assert os.path.exists(expected_folder) == True


def test_create_user_converts_author_to_user_format():
    author = "John Doe"
    expected_user = "John_Doe"

    assert create_user(author) == expected_user


def test_create_user_folder():
    author = "Jane Smith"
    expected_folder = os.path.join("work", "Jane_Smith")

    assert os.path.exists(expected_folder) == False
    assert create_user_folder(author) == expected_folder
    assert os.path.exists(expected_folder) == True


def test_add_txt_filename():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    add_txt_filename(book_dict, book_dict.book_file)

    assert book_dict.txt_file == "test_file.txt"


def test_convert_book_file_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    with pytest.raises(Exception):
        convert_book_file(book_dict)


def test_convert_raises_exception_file_does_not_exist():
    file_path = "non_existent_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    with pytest.raises(Exception):
        convert(file_path, limited_metadata)


def test_create_book_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"

    with pytest.raises(Exception):
        create_book(book_dict)


def test_create_limited_metadata():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"

    assert create_limited_metadata(book_dict) == {
        "title": "Test Title",
        "author": "John Doe",
    }


def test_create_lorebinder():
    book = MagicMock()
    ai_model = MagicMock()

    with patch("your_module.Binder") as mock_binder:
        create_lorebinder(book, ai_model)

    mock_binder.assert_called_once_with(book, ai_model)


def test_convert():
    file_path = "test_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    with patch("lorebinders.main.convert_file") as mock_convert_file:
        convert(file_path, limited_metadata)

    mock_convert_file.assert_called_once_with(file_path, limited_metadata)


def test_create_book():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"

    assert isinstance(create_book(book_dict), Book)
