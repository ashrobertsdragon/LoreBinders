import os

from character_analysis import analyze_book
from make_pdf import create_pdf
from send_email import send_mail

if not os.path.exists(".replit"):
  from dotenv import load_dotenv
  load_dotenv()

def main():

  book_file = "DragonRun.txt" # placeholder
  narrator = "Kalia" # placeholder
  user = "ashdragon" # placeholder
  user_email = os.getenv("user_email") # placeholder

  user_folder = os.path.join("ProsePal", "users", user)
  book_name, _ = os.path.splitext(book_file)

  folder_name = analyze_book(user_folder, book_file, narrator)
  create_pdf(folder_name, book_name)
  send_mail(folder_name, book_name, user_email)

if __name__ == "__main__":
  main()
