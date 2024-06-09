import os
from typing import List, Optional


def get_narrator() -> str:
    """
    Checks if the book was written in third person and ask's for the
    narrator's name if not.

    Returns:
        narrator (str): The name of the narrator or "" if book is in
            third-person.
    """
    valid_input: bool = False
    while not valid_input:
        third_p_input: str = input(
            "Is the book written in third person? Y/n > "
        )
        if third_p_input.upper().startswith("Y"):
            is_third: bool = True
        elif third_p_input.lower().startswith("n"):
            is_third = False

    if is_third:
        return ""
    else:
        return input(
            "Enter narrator's name as identified by most of the "
            "characters in the story > "
        )


def get_attributes(attribute_type: Optional[str] = None) -> list:
    """
    Asks for additional attributes and returns them as a list.

    Args:
        attribute_type (str): Optional.  If set, the function returns a list
            for a specific attribute type. If None, the attribute type is
            "other attributes"

    Returns:
        A list of user inputted attributes.
    """
    if attribute_type is None:
        input_label = "category"
    else:
        input_label = f"{attribute_type} trait"
    attribute_list: List[str] = []
    while True:
        attribute = input(
            f"Enter additional {input_label} or press D for done > "
        )
        if attribute.upper().strip() == "D":
            break
        attribute_list.append(attribute)
    return attribute_list


def parse_file_path(path) -> str:
    path_parts: str = path.split("/") if "/" in path else path.split("\\")
    return os.path.join(path_parts)


def input_title() -> str:
    return input("Enter book title > ")


def input_author() -> str:
    return input("Enter author name > ")


def input_book_path() -> str:
    file_path: str = input(
        "Enter the absolute path to the ebook to process > "
    )
    return parse_file_path(file_path)


def get_inputs() -> dict:
    title: str = input_title()
    author: str = input_author()
    book_path = input_book_path()
    narrator: str = get_narrator()
    character_attributes: list = get_attributes("character")
    other_categories: list = get_attributes()

    return {
        "title": title,
        "author": author,
        "book_file": book_path,
        "narrator": narrator,
        "character_attributes_list": character_attributes,
        "other_categories_list": other_categories,
    }


def get_book() -> dict:
    book_dict: dict = get_inputs()
    return confirm_inputs(book_dict)


def confirm_inputs(book_dict: dict) -> dict:
    """
    Displays the book metadata in a user-friendly format, allows editing, and
    returns the final data.

    Args:
        book_dict (dict): The dictionary containing book metadata.

    Returns:
        dict: The updated book_dict dictionary.
    """

    key_name_map = {
        "title": "Title",
        "author": "Author",
        "book_file": "Book File Path",
        "narrator": "Narrator",
        "character_attributes": "Character Attributes (List)",
        "other_attributes": "Other Attributes (List)",
    }

    def edit_book_dict(key_name):
        """
        Edits the specified key in the book_dict dictionary using the
        appropriate input function.

        Args:
            key_name (str): The name of the key to edit.
        """
        input_function = {
            "title": input_title,
            "author": input_author,
            "narrator": get_narrator,
            "book_file": input_book_path,
            "character_attributes": get_attributes("characters"),
            "other_attributes": get_attributes(),
        }
        new_value = input_function[key_name]()
        book_dict[key_name] = new_value

    while True:
        print("\nBook book_dict:")
        for key, value in book_dict.items():
            key_name = key_name_map[key]
            print(f"  - {key_name}: {value}")

        choice = input(
            "\nIf this is correct, type Y to continue. "
            "Otherwise, enter the item you wish to change > "
        ).lower()

        if choice.upper() == "Y":
            return book_dict

        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(book_dict):
                key_name = list(book_dict.keys())[index]
                edit_book_dict(key_name)
            else:
                print(
                    "Invalid index." "Please enter a valid number or key name."
                )
        else:
            key_name = choice.strip()
            if key_name in key_name_map.keys():
                edit_book_dict(key_name)
            else:
                print(
                    "Invalid key name."
                    "Please enter a valid number or key name."
                )
