from __future__ import annotations

import os
from typing import Callable

from lorebinders._decorators import required_string
from lorebinders.book_dict import BookDict


@required_string
def get_is_third_person() -> str:
    """
    Prompt the user to input whether the book is written in third person.

    """
    return input("Is the book written in third person? Y/n > ")


def is_third_person() -> bool:
    """
    Check if the user input indicates third person perspective.

    Returns:
        True if the input starts with 'Y' (case insensitive),
        False if it starts with 'N',and continues to prompt the user until a
            valid input is provided.
    """
    valid_input: bool = False
    while not valid_input:
        third_p_input = get_is_third_person()
        if third_p_input.upper().startswith("Y"):
            return True
        elif third_p_input.lower().startswith("n"):
            return False
        else:
            print("Invalid input, please try again.")
            continue
    return False  # shut MyPy up


def get_narrator() -> str:
    """
    Checks if the book was written in third person and ask's for the
    narrator's name if not.

    Returns:
        narrator (str): The name of the narrator or "" if book is in
            third-person.
    """

    if is_third_person():
        return ""
    else:
        return input(
            "Enter narrator's name as identified by most of the "
            "characters in the story > "
        )


def set_input_label(attribute_type: str | None = None) -> str:
    """
    Sets the input label based on the attribute type
    """
    return "category" if attribute_type is None else f"{attribute_type} trait"


def get_attributes(attribute_type: str | None = None) -> list:
    """
    Asks for additional attributes and returns them as a list.

    Args:
        attribute_type (str): Optional.  If set, the function returns a list
            for a specific attribute type. If None, the attribute type is
            "other attributes"

    Returns:
        A list of user inputted attributes.
    """
    input_label = set_input_label(attribute_type)
    attribute_list: list[str] = []
    while True:
        attribute = input(
            f"Enter additional {input_label} or press D for done > "
        )
        if attribute.upper().strip() == "D":
            break
        attribute_list.append(attribute)
    return attribute_list


def parse_file_path(path: str) -> str:
    """
    Extract the individual parts of the path.
    """
    path_parts = path.split("/") if "/" in path else path.split("\\")
    parts_tuple = tuple(path_parts)
    return os.path.join(*parts_tuple)


@required_string
def input_title() -> str:
    return input("Enter book title > ")


@required_string
def input_author() -> str:
    return input("Enter author name > ")


@required_string
def input_book_path() -> str:
    file_path: str = input(
        "Enter the absolute path to the ebook to process > "
    )
    return parse_file_path(file_path)


def get_inputs() -> BookDict:
    title: str = input_title()
    author: str = input_author()
    book_path = input_book_path()
    narrator: str = get_narrator()
    character_attributes: list = get_attributes("character")
    other_categories: list = get_attributes()

    return BookDict(
        title=title,
        author=author,
        book_file=book_path,
        narrator=narrator,
        character_traits=character_attributes,
        custom_categories=other_categories,
    )


def display_book_metadata(book_dict: BookDict, key_name_map: dict) -> None:
    """
    Prints the book metadata in a user-friendly format.

    Args:
        book_dict (BookDict): The dictionary containing book metadata.
        key_name_map (dict): A dictionary mapping keys to user-friendly names.
    """
    print("\nBook metadata:")
    for key, value in key_name_map.items():
        print(f"  - {value}: {getattr(book_dict, key)}")


def get_user_choice(key_name_map: dict) -> str:
    """
    Prompts the user for a choice and returns the user's input.

    Args:
        key_name_map (dict): A dictionary mapping keys to user-friendly names.

    Returns:
        str: The user's input.
    """
    return input(
        "\nIf this is correct, type Y to continue. "
        "Otherwise, enter the item you wish to change > "
    ).lower()


def edit_book_dict(
    book_dict: BookDict, key_name: str, input_function: Callable
) -> None:
    """
    Edits the specified key in the book_dict dictionary using the provided
    input function.

    Args:
        book_dict (BookDict): The dictionary containing book metadata.
        key_name (str): The name of the key to edit.
        input_function (Callable): The function to call to get the new value
        for the key.
    """
    new_value = input_function()
    setattr(book_dict, key_name, new_value)


def confirm_inputs(book_dict: BookDict) -> BookDict:
    """
    Displays the book metadata in a user-friendly format, allows editing, and
    returns the final data.

    Args:
        book_dict (dict): The dictionary containing book metadata.

    Returns:
        dict: The updated book_dict dictionary.
    """
    key_name_map = {
        "book_file": "Book File Path",
        "title": "Title",
        "author": "Author",
        "narrator": "Narrator",
        "character_traits": "Character Traits (List)",
        "custom_categories": "Other Categories (List)",
    }

    input_function_map = {
        "title": input_title,
        "author": input_author,
        "narrator": get_narrator,
        "book_file": input_book_path,
        "character_traits": lambda: get_attributes("characters"),
        "custom_categories": get_attributes,
    }

    while True:
        display_book_metadata(book_dict, key_name_map)
        choice = get_user_choice(key_name_map)

        if choice.upper() == "Y":
            return book_dict

        elif choice in key_name_map:
            edit_book_dict(book_dict, choice, input_function_map[choice])
        else:
            print("Please enter a valid number or key name.")


def get_book() -> BookDict:
    book_dict = get_inputs()
    return confirm_inputs(book_dict)
