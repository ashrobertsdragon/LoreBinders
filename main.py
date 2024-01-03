import os

from character_analysis import analyze_book
from convert_file import convert_file
from make_pdf import create_pdf
from send_email import send_mail

if not os.path.exists(".replit"):
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

def main():

  book_file = "DragonRun.txt" # placeholder
  narrator = "Kalia" # placeholder
  user = "ashdragon" # placeholder
  user_email = os.getenv("user_email") # placeholder
  metadata = "" # placeholder

  user_folder = os.path.join("ProsePal", "users", user)
  book_name, _ = os.path.splitext(book_file)

  if not metadata:
    author, title = extract_metadata(user_folder, book_name)
    metadata = {"title": title, "author": author}

  convert_file(user_folder, book_file, metadata)
  folder_name = analyze_book(user_folder, book_file, narrator)
  create_pdf(folder_name, book_name)
  send_mail(folder_name, book_name, user_email)

if __name__ == "__main__":
  main()
