import characteranalysis

def main():

  user = "ashdragon" # placeholder
  user_folder = f"users/{user}"

  #book_name = input("Enter the file name of the book (including the .txt extension): ")
  book_name = "blue_dragoneer1.txt"

  file_path = f"{user_folder}/{book_name}"

  characteranalysis.analyze_book(user_folder, file_path)

if __name__ == "__main__":
  main()
