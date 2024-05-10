import os
def append_to_dict_list(dictionary, key, value):
  "Appends value to list of values in dictionary"

  if key in dictionary:
      dictionary[key].append(value)
  else:
      dictionary[key] = [value]

def clear_screen():
  "Clears the the screen using OS-specific commands"

  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def is_valid_json(file_path: str) -> bool:
  "Checks to see if JSON file exists and is non-empty"

  if os.path.exists(file_path):
    return bool(read_json_file(file_path))
  return False
