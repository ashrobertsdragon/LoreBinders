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
