from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BookDict:
    book_file: str
    title: str
    author: str
    narrator: Optional[str] = None
    character_traits: Optional[List[str]] = None
    custom_categories: Optional[List[str]] = None
    user_folder: Optional[str] = None
    txt_file: Optional[str] = None

    def set_user_folder(self, user_folder: str) -> None:
        self.user_folder = user_folder

    def set_txt_file(self, txt_file: str) -> None:
        self.txt_file = txt_file
