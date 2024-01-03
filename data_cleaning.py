import os
import re
from typing import Tuple

import common_functions as cf


TITLES = [
  "admiral", "airman", "ambassador", "aunt", "baron", "baroness", "brother", "cadet",
  "cap", "captain", "col", "colonel", "commander", "commodore", "corporal", "count",
  "countess", "cousin", "dad", "daddy", "doc", "doctor", "dr", "duchess", "duke",
  "earl", "ensign", "father", "gen", "general", "granddad", "grandfather", "grandma",
  "grandmom", "grandmother", "grandpop", "great aunt", "great grandfather",
  "great grandmother", "great uncle", "great-aunt", "great-grandfather",
  "great-grandmother", "great-uncle", "king", "lady", "leftenant", "lieutenant",
  "lord", "lt", "ma", "ma'am", "madam", "major", "marquis", "miss", "missus", "mister",
  "mjr", "mom", "mommy", "mother", "mr", "mrs", "ms", "nurse", "pa", "pfc", "pop",
  "prince", "princess", "private", "queen", "sarge", "seaman", "sergeant", "sir",
  "sister", "uncle"
  ]

def compare_names(inner_values: list, name_map: dict) -> list:

  for i, value_i in enumerate(inner_values):
    value_i_split = value_i.split()
    if value_i_split[0] in TITLES and value_i not in TITLES:
      value_i = ' '.join(value_i_split[1:])

    for j, value_j in enumerate(inner_values):
      if i != j and value_i != value_j and not value_i.endswith(")") and not value_j.endswith(")") and (value_i.startswith(value_j) or value_i.endswith(value_j)):
        value_j_split = value_j.split()
        if value_j_split[0] in TITLES and value_j not in TITLES:
          value_j = ' '.join(value_j_split[1:])
          if value_i in value_j or value_j in value_i:
            if value_i.endswith('s') and not value_j.endswith('s'):
              value_i = value_i[:-1]
            elif value_j.endswith('s') and not value_i.endswith('s'):
              value_j = value_j[:-1]
          shorter_value, longer_value = sorted([value_i, value_j], key = len)
          name_map.setdefault(shorter_value, longer_value)
          name_map.setdefault(longer_value, longer_value)
  standardized_names = [name_map.get(name, name) for name in inner_values]
  return list(dict.fromkeys(standardized_names))

def sort_names(character_lists: list, narrator: str) -> dict:

  parse_tuples = {}
  attribute_table = {}
  name_map = {}

  character_info_pattern = re.compile(r"\((?!interior|exterior).+\)$", re.IGNORECASE)
  inverted_setting_pattern = re.compile(r"(interior|exterior)\s+\((\w+)\)", re.IGNORECASE)
  leading_colon_pattern = re.compile(r"\s*:\s+")
  list_formatting_pattern = re.compile(r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t")
  missing_newline_before_pattern = re.compile(r"(?<=\w)(?=[A-Z][a-z]*:)")
  missing_newline_between_pattern = re.compile(r"(\w+ \(\w+\))\s+(\w+)")
  missing_newline_after_pattern = re.compile(r"(?<=\w):\s*(?=\w)")
  junk_lines = ["additional", "note", "none"]
  stop_words = ["mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main", "him", "her", "I", "</s>", "a"]

  for chapter_index, proto_dict in character_lists:
    if chapter_index not in parse_tuples:
      parse_tuples[chapter_index] = proto_dict
    else:
      parse_tuples[chapter_index] += "\n" + proto_dict

  for chapter_index, proto_dict in parse_tuples.items():

    attribute_table[chapter_index] = {}
    inner_dict = {}
    attribute_name = None
    inner_values = []
    lines = proto_dict.split("\n")

    i = 0
    while i < len(lines):
      line = lines[i]
      line = list_formatting_pattern.sub("", line)
      line = re.sub(r'(interior|exterior)', lambda m: m.group().lower(), line, flags=re.IGNORECASE)
      if line.startswith("interior:") or line.startswith("exterior:"):
        prefix, places = line.split(":", 1)
        setting = "(interior)" if prefix == "interior" else "(exterior)"
        split_lines = [f"{place.strip()} {setting}" for place in places.split(",")]
        lines[i:i + 1] = split_lines
        continue
      line = inverted_setting_pattern.sub(r"\2 (\1)", line)
      if ", " in line:
        comma_split = line.split(", ")
        lines[i:i + 1] = comma_split
        continue
      added_newline = missing_newline_before_pattern.sub("\n", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue
      added_newline = missing_newline_between_pattern.sub(r"\1\n\2", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue
      added_newline = missing_newline_after_pattern.sub(":\n", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue
      line = leading_colon_pattern.sub("", line)
      line = line.strip()
      if line == "":
        i += 1
        continue
      if line.lower() in [word.lower() for word in stop_words]:
          i += 1
          continue
      if any(junk in line.lower() for junk in junk_lines):
        i += 1
        continue
      if line.count("(") != line.count(")"):
        line.replace("(", "").replace(")", "")
      if line.lower() == "setting:":
        line = "Settings:"
      line = re.sub(r"narrator", narrator, line, flags=re.IGNORECASE)
      line = character_info_pattern.sub("", line)

      #Remaining lines ending with a colon are attribute names and lines following belong in a list for that attribute
      if line.endswith(":"):
        if attribute_name:
          inner_dict.setdefault(attribute_name, []).extend(inner_values)
          inner_values = []
        attribute_name = line[:-1].title()
      else:
        inner_values.append(line)
      i += 1

    if attribute_name:
      inner_dict.setdefault(attribute_name, []).extend(inner_values)
      inner_values = []
    if inner_dict:
      for attribute_name, inner_values in inner_dict.items():
        if attribute_name.endswith("s") and attribute_name[:-1] in inner_dict:
          inner_values.extend(inner_dict[attribute_name[:-1]])
          inner_dict[attribute_name[:-1]] = []
        inner_values = compare_names(inner_values, name_map)
        attribute_table[chapter_index][attribute_name] = inner_values
      inner_values = []
  # Remove empty attribute_name keys
  for chapter_index in list(attribute_table.keys()):
    for attribute_name, inner_values in list(attribute_table[chapter_index].items()):
      if not inner_values:
        del attribute_table[chapter_index][attribute_name]
  return attribute_table

def remove_none_found(d):
  if isinstance(d, dict):
    new_dict = {}
    for key, value in d.items():
      cleaned_value = remove_none_found(value)
      if cleaned_value != "None found":
        new_dict[key] = cleaned_value
    return new_dict
  elif isinstance(d, list):
    return [remove_none_found(item) for item in d]
  else:
    return d

def final_reshape(chapter_summaries: dict, folder_name: str) -> None:
  """
  Demotes chapter numbers to lowest dictionary in Characters and Settings dictionaries.
  
  Argument:
  folder_name: A string containing the path to the folder containing the chapter summaries.
  """

  reshaped_data = {}

  for attribute, names in chapter_summaries.items():
    if attribute not in ["Characters", "Settings"]:
      reshaped_data[attribute] = names
      continue
    reshaped_data[attribute] = {}
    for name, chapters in names.items():
      reshaped_data[attribute][name] = {}
      for chapter, traits in chapters.items():
        if not isinstance(traits, dict):
          reshaped_data[attribute][name][chapter] = traits
          continue
        for trait, detail in traits.items():
          if trait not in reshaped_data[attribute][name]:
            reshaped_data[attribute][name][trait] = {}
          reshaped_data[attribute][name][trait][chapter] = detail
  cf.write_json_file(reshaped_data, os.path.join(folder_name, "lorebinder.json"))

def sort_dictionary(attribute_summaries: dict) -> dict:
  "Sorts dictionary keys"

  sorted_dict = {}

  for outer_key, nested_dict in attribute_summaries.items():
    middle_dict = {key: nested_dict[key] for key in sorted(nested_dict)}
    for key, inner_dict in middle_dict.items():
      if isinstance(inner_dict, dict):
        sorted_inner_dict = {str(inner_key): inner_dict[str(inner_key)]
                            for inner_key in sorted(map(int, inner_dict.keys()))}
        middle_dict[key] = sorted_inner_dict
    sorted_dict[outer_key] = middle_dict

  return sorted_dict


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
  return plural[:-1]

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
  elif isinstance(value1, list) and isinstance(value2, dict):
    for k, v in value2.items():
      if k in value1:
        value1[k] = merge_values(value1[k], v)
      else:
        value1.append({k: v})
  elif isinstance(value1, dict) and isinstance(value2, list):
    if "Also" in value1:
      value1["Also"].extend(value2)
    else:
      value1["Also"] = value2
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

def deduplicate_across_dictionaries(attribute_summaries: dict) -> dict:
  "Finds dupicates across dictionaries"

  characters_dict = attribute_summaries.get("Characters", {})

  for attribute, names in attribute_summaries.items():
    if attribute == "Characters":
      continue
    for name in list(names.keys()):
      if name not in characters_dict:
        continue
      for chapter, details in names[name].items():
        if chapter in characters_dict[name]:
          merged_values = merge_values(characters_dict[name][chapter], details)
          attribute_summaries["Characters"][name][chapter] = merged_values
        elif isinstance(details, dict):
          attribute_summaries["Characters"][name][chapter] = details
        else:
          attribute_summaries["Characters"][name][chapter] ={"Also": details}
      del names[name]

  return attribute_summaries

def remove_titles(key: str) -> str:
  "Removes words in TITLES list from key"

  key_words = key.split()
  de_titled = [word for word in key_words if word.lower().strip(".,") not in TITLES]
  return " ".join(de_titled)

def is_title(key: str) -> bool:
  return any(title == key.lower() for title in TITLES)

def prioritize_keys(key1: str, key2: str) -> Tuple[str, str]:
  "Determines priority of keys, based on whether one is standalone title or length"
  "Order is lower priority, higher priority"

  key1_is_title = is_title(key1)
  key2_is_title = is_title(key2)
  lower_key1 = key1.lower()
  lower_key2 = key2.lower()

  if (lower_key1 in lower_key2 or lower_key2 in lower_key1) and lower_key1 != lower_key2:
    if key1_is_title:
      return key2, key1
    if key2_is_title:
      return key1, key2
  return sorted([key1, key2], key = len)

def is_similar_key(key1: str, key2: str) -> bool:
  "Determines if two keys are similar"

  detitled_key1 = remove_titles(key1)
  detitled_key2 = remove_titles(key2)
  singular_key1 = to_singular(key1)
  singular_key2 = to_singular(key2)

  if (
      key1 + " " in key2
      or key2 + " " in key1
      or key1 == singular_key2
      or singular_key1 == key2
  ):
    return True

  key1_is_title = is_title(key1)
  key2_is_title = is_title(key2)
  if key1_is_title and key1.lower() in key2.lower():
    return True
  if key2_is_title and key2.lower() in key1.lower():
    return True
  
  if detitled_key1 and detitled_key2:
    return (
      detitled_key1 == key2
      or key1 == detitled_key2
      or detitled_key1 == singular_key2
      or singular_key1 == detitled_key2
      or detitled_key1 + " " in key2
      or detitled_key2 + " " in key1
      or key1 + " " in detitled_key2
      or key2 + " " in detitled_key1
    )

def deduplicate_keys(dictionary:dict) -> dict:
  """
  Removes duplicate keys in a dictionary by merging singular and plural forms of keys.

  Arguments:
    dictionary: The dictionary to deduplicate.
  
  Returns the deduplicated dictionary.
  """

  cleaned_dict = {}

  for outer_key, nested_dict in dictionary.items():
    if not isinstance(nested_dict, dict):
      continue
    duplicate_keys = []
    inner_dict = {}

    for key1 in nested_dict:
      if key1 in duplicate_keys:
        continue
      for key2 in nested_dict:
        if key2 in duplicate_keys or key1 == key2:
          continue
        if is_similar_key(key1, key2):
          key_to_merge, key_to_keep = prioritize_keys(key1, key2)
          nested_dict[key_to_keep] = merge_values(nested_dict[key_to_keep],
                                                  nested_dict[key_to_merge])
          duplicate_keys.append(key_to_merge)

    for key, value in nested_dict.items():
      if key in duplicate_keys:
        continue
      inner_dict[key] = value
    cleaned_dict[outer_key] = inner_dict
  deduplicated_dict = deduplicate_across_dictionaries(cleaned_dict)
  return deduplicated_dict

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
      section = section.title()
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
    cleaned_data[key] = cf.check_json(json_data[key])
  return cleaned_data

def data_cleaning(folder_name: str, chapter_summary: dict) -> dict:
  """
  Cleans the json data and writes it to a new file, reshapes the dictionary to 
  demote chapter numbers inside of attribute names, and merges duplicate keys
  """
  
  destrung_path = os.path.join(folder_name, "chapter_summaries_destrung.json")
  only_found_path = os.path.join(folder_name, "chapter_summaries_only_found.json")
  reshaped_path = os.path.join(folder_name, "chapter_summaries_reshaped.json")
  deduplicated_path = os.path.join(folder_name, "chapter_summaries_deduplicated.json")
  chapter_summaries_path = os.path.join(folder_name, "chapter_summaries.json")

  if not os.path.exists(destrung_path):
    destrung_json = de_string_json(chapter_summary)
    cf.write_json_file(destrung_json, destrung_path)
  else:
    destrung_json = cf.read_json_file(destrung_path)

  if not os.path.exists(reshaped_path):
    reshaped_dict = reshape_dict(destrung_json)
    cf.write_json_file(reshaped_dict, reshaped_path)
  else:
    reshaped_dict = cf.read_json_file(reshaped_path)

  if not os.path.exists(only_found_path):
    only_found = remove_none_found(reshaped_dict)
    cf.write_json_file(only_found, only_found_path)
  else:
    only_found = cf.read_json_file(only_found_path)

  if not os.path.exists(deduplicated_path):
    dedpulicated_dict = deduplicate_keys(only_found)
    cf.write_json_file(dedpulicated_dict, deduplicated_path)
  else:
    dedpulicated_dict = cf.read_json_file(deduplicated_path)

  if not os.path.exists(chapter_summaries_path):
    sorted_dictionary = sort_dictionary(dedpulicated_dict)
    cf.write_json_file(sorted_dictionary, chapter_summaries_path)
  else:
    sorted_dictionary = cf.read_json_file(chapter_summaries_path)

  return sorted_dictionary
