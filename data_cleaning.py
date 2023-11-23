import json
import re

import common_functions as cf


def to_singular(plural: str) -> str:
  """
    Converts a plural word to its singular form based on common English pluralization rules.
    
    Argument:
    plural: A string representing the plural form of a word.
    
    Returns the singular form of the given word if a pattern matches, otherwise the original word.
    """
    
  patterns = {
    r'(\w+)(ves)$': r'\1f',
    r'(\w+)(ies)$': r'\1y',
    r'(\w+)(s)$': r'\1[^s]',
    r'(\w+)(i)$': r'\1us',
    r'(\w+)(a)$': r'\1um',
    r'(\w+)(en)$': r'\1an',
    r'(\w+)(oes)$': r'\1o',
    r'(\w+)(ses)$': r'\1s',
    r'(\w+)(hes)$': r'\1h',
    r'(\w+)(xes)$': r'\1x',
    r'(\w+)(zes)$': r'\1z'
  }

  for pattern, repl in patterns.items():
    singular = re.sub(pattern, repl, plural)
    if plural != singular:


      return singular


    return plural 

def merge_values(value1, value2):
  """
  Merges two dictionary key values of unknown datatypes into one
  Arguments:
    value1: A dictionary key value
    value2: A dictionary key value

  Returns merged dictionary key value
  """

  if isinstance(value1, dict) and isinstance(value2, dict):
    for k, v in value2.items():
      if k in value1:
        value1[k] = merge_values(value1[k], v)
      else:
        value1[k] = v
        
  elif isinstance(value1, list) and isinstance(value2, list):
    value1.extend(value2)

  elif isinstance(value1, dict):
    for key in value1:
      if key == value2:


        return value1

    value1["Also"] = value2
    
  elif isinstance(value2, list):
    value2.append(value1)


    return value2
    
  else:


    return [value1, value2]

  return value1
    
def deduplicate_keys(dictionary:dict) -> dict:
  """
  Removes duplicate keys in a dictionary by merging singular and plural forms of keys.

  Arguments:
    dictionary: The dictionary to deduplicate.
  
   Returns the deduplicated dictionary.
    """

  duplicate_keys = []

  for key in dictionary:
    singular_form = to_singular(key)
    if singular_form != key and singular_form in dictionary:
      merge_values(dictionary[key], dictionary[singular_form])
      duplicate_keys.append(singular_form)

  for key in duplicate_keys:
    del dictionary[key]


  return dictionary

def reshape_dict(chapter_summaries: dict) -> dict:
  """
  Reshapes a dictionary of chapter summaries to demote chapter numbers inside attribute names.

  Arguments:
    chapter_summaries: Dictionary containing chapter summaries.
  
  Returns a reshaped dictionary.
  """

  reshaped_data = {}

  for chapter, chapter_data in chapter_summaries.items():
    for section, section_data in chapter_data.items():
      if section not in reshaped_data:
        reshaped_data[section] = {}

      for entity, entity_details in section_data.items():
        if isinstance(entity_details, dict):
          for key, value in entity_details.items():
            reshaped_data[section].setdefault(entity, {}).setdefault(chapter, {}).setdefault(key, []).append(value)

        elif isinstance(entity_details, str):
          reshaped_data[section].setdefault(entity, {}).setdefault(chapter, []).append(entity_details)

  return reshaped_data

def de_string_json(json_data):
  """
  Parses string representations of JSON data into Python dictionary objects.

  Arguments:
    json_data: Dictionary with string representations of JSON data.
    
  Returns dictionary with parsed JSON data.
  """

  cleaned_data = {}

  for key in json_data:
    cleaned_data[key] = json.loads(json_data[key])


  return cleaned_data

def data_cleaning(folder_name: str):
  """
  Cleans the json data and writes it to a new file, reshapes the dictionary to demote chapter numbers inside of attribute names, and merges duplicate keys
  """
  
  chapter_summaries = cf.read_json_file(f"{folder_name}/chapter_summary.json")
  print("json read")

  cleaned_json = de_string_json(chapter_summaries)
  print("json cleaned")
  
  reshaped_data = reshape_dict(cleaned_json)
  print("reshaped")
  dedpulicated_dictionary = deduplicate_keys(reshaped_data)
  print("dedpulicated")
  cf.write_json_file(dedpulicated_dictionary, f"{folder_name}/chapter_summaries.json")
  print("new json  file written")
  