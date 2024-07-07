import os
from unittest.mock import patch

import pytest

from lorebinders.book_dict import BookDict
from lorebinders.user_input import (
    confirm_inputs,
    display_book_metadata,
    edit_book_dict,
    get_attributes,
    get_book,
    get_inputs,
    get_narrator,
    get_user_choice,
    input_author,
    input_book_path,
    input_title,
    parse_file_path,
)



@pytest.fixture
def book_dict():
    return BookDict(
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        book_file="/home/user/book.epub",
        narrator="Nick Carraway",
        character_traits=["Wealth", "Social Status"],
        custom_categories=["Social Classes", "Themes"],
    )


@pytest.fixture
def key_name_map() -> dict:
    return {
        "book_file": "Book File Path",
        "title": "Title",
        "author": "Author",
        "narrator": "Narrator",
        "character_traits": "Character Traits (List)",
        "custom_categories": "Other Categories (List)",
    }

def test_get_narrator_third_person():
    with patch("builtins.input", side_effect=["Y"]):
        assert get_narrator() == ""


def test_get_narrator_not_third_person():
    with patch("builtins.input", side_effect=["n", "Nick Carraway"]):
        assert get_narrator() == "Nick Carraway"


def test_get_narrator_invalid_input():
    with patch("builtins.input", side_effect=["x", "Y"]):
        assert get_narrator() == ""


def test_get_attributes_character_traits():
    inputs = ["Wealth", "Status", "D"]
    with patch("builtins.input", side_effect=inputs):
        assert get_attributes("character") == ["Wealth", "Status"]


def test_get_attributes_custom_categories():
    inputs = ["Social Classes", "Political Factions", "D"]
    with patch("builtins.input", side_effect=inputs):
        assert get_attributes() == ["Social Classes", "Political Factions"]


def test_get_attributes_invalid_input():
    with patch("builtins.input", side_effect=["", "D"]):
        assert get_attributes("character") == [""]


def test_parse_file_path_unix():
    path = "/home/user/book.epub"
    expected = os.path.normpath("/home/user/book.epub")
    assert parse_file_path(path) == expected


def test_parse_file_path_windows():
    path = r"C:\Users\User\book.epub"
    expected = os.path.normpath(r"C:\Users\User\book.epub")
    assert parse_file_path(path) == expected


def test_input_title():
    with patch("builtins.input", side_effect=["The Great Gatsby"]):
        assert input_title() == "The Great Gatsby"


def test_input_author():
    with patch("builtins.input", side_effect=["F. Scott Fitzgerald"]):
        assert input_author() == "F. Scott Fitzgerald"


def test_input_book_path():
    with patch("builtins.input", side_effect=["/home/user/book.epub"]):
        expected = os.path.normpath("/home/user/book.epub")
        assert input_book_path() == expected


def test_get_inputs():
    inputs = [
        "The Great Gatsby",  # title
        "F. Scott Fitzgerald",  # author
        "/home/user/book.epub",  # path
        "n",
        "Nick Carraway",  # narrator
        "Wealth",
        "Social Status",
        "D",  # character traits
        "Social Classes",
        "Locations",
        "D",  # custom categories
    ]
    with patch("builtins.input", side_effect=inputs):
        book_dict = get_inputs()
        assert book_dict.title == "The Great Gatsby"
        assert book_dict.author == "F. Scott Fitzgerald"
        assert book_dict.book_file == os.path.normpath("/home/user/book.epub")
        assert book_dict.narrator == "Nick Carraway"
        assert book_dict.character_traits == ["Wealth", "Social Status"]
        assert book_dict.custom_categories == ["Social Classes", "Locations"]


def test_display_book_metadata(book_dict, key_name_map, capsys):
    display_book_metadata(book_dict, key_name_map)
    captured = capsys.readouterr()
    expected_output = (
        "\nBook metadata:\n"
        "  - Book File Path: /home/user/book.epub\n"
        "  - Title: The Great Gatsby\n"
        "  - Author: F. Scott Fitzgerald\n"
        "  - Narrator: Nick Carraway\n"
        "  - Character Traits (List): ['Wealth', 'Social Status']\n"
        "  - Other Categories (List): ['Social Classes', 'Themes']\n"
    )
    assert captured.out == expected_output


def test_get_user_choice_edit():
    with patch("builtins.input", return_value="title"):
        assert get_user_choice(key_name_map) == "title"


def test_edit_book_dict(book_dict):
    with patch("builtins.input", return_value="New Title"):
        edit_book_dict(book_dict, "title", input)
        assert book_dict.title == "New Title"


def test_confirm_inputs_correct(book_dict):
    with patch("builtins.input", side_effect=["Y"]):
        assert confirm_inputs(book_dict) == book_dict


def test_confirm_inputs_edit(book_dict):
    inputs = ["title", "New Title", "Y"]
    with patch("builtins.input", side_effect=inputs):
        updated_dict = confirm_inputs(book_dict)
        assert updated_dict.title == "New Title"


def test_get_book():
    inputs = [
        "The Great Gatsby",  # title
        "F. Scott Fitzgerald",  # author
        "/home/user/book.epub",  # path
        "n",
        "Nick Carraway",  # narrator
        "Wealth",
        "Social Status",
        "D",  # character traits
        "Social Classes",
        "Locations",
        "D",  # custom categories
        "Y",  # confirm inputs
    ]
    with patch("builtins.input", side_effect=inputs):
        book_dict = get_book()
        assert book_dict.title == "The Great Gatsby"
        assert book_dict.author == "F. Scott Fitzgerald"
        assert book_dict.book_file == os.path.normpath("/home/user/book.epub")
        assert book_dict.narrator == "Nick Carraway"
        assert book_dict.character_traits == ["Wealth", "Social Status"]
        assert book_dict.custom_categories == ["Social Classes", "Locations"]
