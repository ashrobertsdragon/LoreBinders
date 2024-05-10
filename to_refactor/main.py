import os

import common_functions as cf
from character_analysis import analyze_book
from convert_file import convert_file
from error_handler import ErrorHandler
from make_pdf import create_pdf
from user_input import get_book

from dotenv import load_dotenv
load_dotenv()
error_handler = ErrorHandler()


def create_folder(user_folder, book_file):

  file_path = os.path.join(user_folder, book_file)
  sub_folder = os.path.basename(book_file).split('.')[0]
  folder_name = os.path.join(user_folder, sub_folder)
  os.makedirs(folder_name, exist_ok = True)
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)
  return folder_name, chapters

def create_user(author: str) -> str:
  names = author.split(" ")
  return "_".join(names)

def main():
  book_dict = get_book()
  book_file = book_dict["book_file"]
  author = book_dict["author"]
  user = create_user(author)

  user_folder = os.path.join("users", user)
  book_name, ext = os.path.splitext(book_file)

  if ext != "txt":
    metadata = {"title": book_dict["title"], "author": author}
    convert_file(user_folder, book_file, metadata)

  folder_name, chapters = create_folder(user_folder, book_file)
  error_handler.set_current_file(folder_name)

  analyze_book(folder_name, chapters, book_dict["narrator"])
  create_pdf(folder_name, book_name)


if __name__ == "__main__":
  main()
