import os

from supabase_db import SupabaseDatabase

import common_functions as cf
from character_analysis import analyze_book
from convert_file import convert_file
from error_handler import ErrorHandler
from make_pdf import create_pdf
from send_email import send_mail

from dotenv import load_dotenv
load_dotenv()

def extract_metadata(user_folder, book_name):
  """
  Extracts author and title from the given file path.
  Arguments:
    file_path: Path of the file.
  Returns tuple containing author and title.
  """
  path_components = user_folder.split(os.sep)
  author = path_components[-2]
  title = book_name
  return author, title

def check_db(check_cols, new_row):
  db = SupabaseDatabase()
  if not db.check_existing("craftbinders", check_cols):
    db.insert_data("craftbinders", new_row)
  else:
    print("Already in database")

def create_folder(user_folder, book_file):

  file_path = os.path.join(user_folder, book_file)
  sub_folder = os.path.basename(book_file).split('.')[0]
  folder_name = os.path.join(user_folder, sub_folder)
  os.makedirs(folder_name, exist_ok = True)
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)
  return folder_name, chapters

def main():

  book_file = "DragonRun.txt" # placeholder
  narrator = "Kalia" # placeholder
  user = "ashdragon" # placeholder
  user_email = os.getenv("user_email") # placeholder
  metadata = {"title": "Dragon Run", "author": "Ash Roberts"} # placeholder

  user_folder = os.path.join("users", user)
  book_name, _ = os.path.splitext(book_file)

  if not metadata:
    author, title = extract_metadata(user_folder, book_name)
    metadata = {"title": title, "author": author}

  convert_file(user_folder, book_file, metadata)
  folder_name, chapters = create_folder(user_folder, book_file)

  new_row = {
    "user": user,
    "user_email": user_email,
    "book_name": book_name,
    "narrator": narrator,
    "metadata": metadata,
    "folder_name": folder_name
  }

  check_cols = {
    "user": user,
    "book_name": book_name
  }

  ErrorHandler.set_current_file(folder_name)
  check_db(check_cols, new_row)

  analyze_book(folder_name, chapters, narrator)
  create_pdf(folder_name, book_name)
  send_mail(folder_name, book_name, user_email)

if __name__ == "__main__":
  main()
