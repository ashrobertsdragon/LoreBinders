import os
import characteranalysis

def main():

  user = "ashdragon" # placeholder
  user_folder = os.path.join("ProsePal", "users", user)

  #book_name = input("Enter the file name of the book (including the .txt extension): ")
  book_name = "DragonRun.txt"

  characteranalysis.analyze_book(user_folder, book_name)

if __name__ == "__main__":
  main()
