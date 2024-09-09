import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from lorebinders.convert_book_file import (
    convert,
    convert_book_file,
    create_folder,
    create_limited_metadata,
    add_txt_filename,
    create_user,
    create_user_folder,
)


@patch("lorebinders.convert_book_file.Path")
def test_create_folder(mock_path):
    user = "test_user"
    base_dir = "work"
    expected_path = "work/test_user"
    mock_path_instance = MagicMock(spec=Path)
    mock_path.return_value = mock_path_instance
    mock_path_instance.__str__.return_value = expected_path

    result = create_folder(user, base_dir)

    assert result == mock_path_instance
    assert str(result) == expected_path
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_create_user_converts_author_to_user_format():
    author = "John Doe"
    expected_user = "John_Doe"

    assert create_user(author) == expected_user


@patch("lorebinders.convert_book_file.create_folder")
def test_create_user_folder(mock_create_folder):
    author = "Jane Smith"
    work_dir = "work"
    expected_folder = os.path.join(work_dir, "Jane_Smith")

    mock_create_folder.return_value = expected_folder
    result = create_user_folder(author, work_dir)

    assert result == expected_folder
    mock_create_folder.assert_called_once_with("Jane_Smith", work_dir)


def test_add_txt_filename():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    add_txt_filename(book_dict, book_dict.book_file)

    assert book_dict.txt_file == "test_file.txt"

@patch("lorebinders.convert_book_file.convert_file")
def test_convert(mock_convert_file):
    file_path = "test_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    convert(file_path, limited_metadata)

    mock_convert_file.assert_called_once_with(file_path, limited_metadata)


def test_convert_book_file_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    with pytest.raises(Exception):
        convert_book_file(book_dict)


def test_create_limited_metadata():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"

    assert create_limited_metadata(book_dict) == {
        "title": "Test Title",
        "author": "John Doe",
    }


@patch("lorebinders.convert_book_file.create_user_folder")
@patch("lorebinders.convert_book_file.convert")
def test_convert_book_file(mock_convert, mock_create_user_folder):
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"
    work_dir = "work"

    mock_create_user_folder.return_value = "/mock/user/folder"

    convert_book_file(book_dict, work_dir)

    mock_create_user_folder.assert_called_once_with("John Doe", work_dir)
    mock_convert.assert_called_once()
    assert book_dict.txt_file == "test_file.txt"

def test_convert_raises_exception_file_does_not_exist():
    file_path = "non_existent_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    with pytest.raises(Exception):
        convert(file_path, limited_metadata)
