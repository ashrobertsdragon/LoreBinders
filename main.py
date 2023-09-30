import os

def main():

  invalid_file = False

  user = "ashdragon" # placeholder
  user_folder = f"users/{user}"

  book_name = input("Enter the file name of the book (including the .txt extension): ")

  file_paths = [os.path.join(user_folder, book_name) for book_name in os.listdir(user_folder) if book_name.endswith('.txt')]
  valid_analysis_type = False

  while not valid_analysis_type:
    analysis_type = int(input("Choose analysis type:\n1. Story Bible\nEnter a number: "))

    if analysis_type == 1:
      import characteranalysis
      characteranalysis.analyze_series(user_folder, file_paths)
      valid_analysis_type = True
    elif analysis_type == 2:
      import plotanalysis
      plotanalysis.analyze_book(user_folder, file_path)
      valid_analysis_type = True
    else:
      print("Invalid analysis type. Please try again.\n")

if __name__ == "__main__":
  main()
