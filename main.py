import os

def main():

  invalid_file = False

  user = "ashdragon"
  user_folder = f"users/{user}"
  while not invalid_file:
    book_path = input("Enter the file name of the book (including the .txt extension): ")
    file_path = f"{user_folder}/{book_path}"
    if not os.path.exists(file_path):
      print(f"Error: File '{file_path}' not found.")
    else:
      invalid_file = True

  valid_analysis_type = False

  while not valid_analysis_type:
    analysis_type = int(input("Choose analysis type:\n1. Story Bible\nEnter a number: "))

    if analysis_type == 1:
      import characteranalysis
      characteranalysis.analyze_book(user_folder, file_path)
      valid_analysis_type = True
    elif analysis_type == 2:
      import plotanalysis
      plotanalysis.analyze_book(user_folder, file_path)
      valid_analysis_type = True
    else:
      print("Invalid analysis type. Please try again.\n")

if __name__ == "__main__":
  main()
