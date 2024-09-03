from dataclasses import dataclass
from typing import Optional


@dataclass
class BookDict:
    book_file: str
    title: str
    author: str
    narrator: Optional[str] = None
    character_traits: Optional[list[str]] = None
    custom_categories: Optional[list[str]] = None
    user_folder: Optional[str] = None
    txt_file: Optional[str] = None

    def set_user_folder(self, user_folder: str) -> None:
        self.user_folder = user_folder

    def set_txt_file(self, txt_file: str) -> None:
        self.txt_file = txt_file
