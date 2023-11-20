import json
import os
import re

from tqdm import tqdm
from typing import Tuple
import common_functions as cf
import data_cleaning

def initialize_names(chapters: list, folder_name: str) -> Tuple[int, list, int, dict, int]:

  num_chapters = len(chapters)
  print(f"\nTotal Chapters: {num_chapters} \n\n")
  character_lists_index = 0
  chapter_summary_index = 0

  character_lists_path = os.path.join(folder_name, "character_lists.json")
  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")

  if os.path.exists(character_lists_path):
    character_lists =  cf.read_json_file(character_lists_path)
    if not isinstance(character_lists, list):
      character_lists = []
      cf.write_json_file(character_lists, character_lists_path)
  else:
    character_lists = []
    cf.write_json_file(character_lists, character_lists_path)
    character_lists_index = len(character_lists)

  if os.path.exists(chapter_summary_path):
    chapter_summary = cf.read_json_file(chapter_summary_path)
    if not isinstance(chapter_summary, dict):
      chapter_summary = {}
      cf.write_json_fie(chapter_summary, chapter_summary_path)
  else:
    chapter_summary = {}
    cf.write_json_file(chapter_summary, chapter_summary_path)
    chapter_summary_index = len(chapter_summary)


  return num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index

def compare_names(inner_values: list, name_map: dict) -> list:

  titles = ["princess", "prince", "king", "queen", "count", "duke", "duchess", "baron", "baroness", "countess", "lord", "lady", "earl", "marquis", "ensign", "private", "sir", "cadet", "sergeant", "lieutenant", "leftenant", "lt", "pfc", "cap", "sarge", "mjr", "col", "gen", "captain", "major", "colonel", "general", "admiral", "ambassador", "commander", "corporal", "airman", "seaman", "commodore", "mr", "mrs", "ms", "miss", "missus", "madam", "mister", "ma'am", "aunt", "uncle", "cousin"]

  for i, value_i in enumerate(inner_values):
    value_i_split = value_i.split()
    if value_i_split[0] in titles:
      value_i = ' '.join(value_i_split[1:])
      
    for j, value_j in enumerate(inner_values):
      if i != j and value_i != value_j and not value_i.endswith(")") and not value_j.endswith(")") and (value_i.startswith(value_j) or value_i.endswith(value_j)):

        value_j_split = value_j.split()
        if value_j_split[0] in titles:
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
  inner_values = list(dict.fromkeys(standardized_names))


  return inner_values

def sort_names(character_lists: list) -> dict:

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
  stop_words = ["mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main", "him", "her", "narrator", "I", "</s>", "a"]

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
      
def get_attributes(folder_name: str) -> Tuple[str, str]:

  dictionary_attributes_list = [] 
  attribute_strings = []
  attributes_path = f"{folder_name}/attributes.json"
  if os.path.exists(attributes_path):
    role_attributes, custom_attributes = cf.read_json_file(attributes_path)


    return role_attributes, custom_attributes

  ask_attributes = input("Besides characters and setting, what other attributes would you like ProsePal to search for (e.g. fantasy races, factions, religions, etc)? Please be as specific as possible. Attributes must be separated by commas for the program to work. Type N if you only want to search for characters and settings\n> ")
  
  if ask_attributes.strip().lower() == "n":
    custom_attributes = ""
    role_attributes = ""
    
  elif ask_attributes.strip() == "":
    custom_attributes = ""
    role_attributes = ""
    
  else:
    custom_attributes = f" and the following additional attributes: {ask_attributes}"
  dictionary_attributes_list = ask_attributes.split(",")

  for attribute in dictionary_attributes_list:
    
    attribute = attribute.strip()
    attribute_string = f"{attribute}:\n{attribute}1\n{attribute}2\n{attribute}3"
    attribute_strings.append(attribute_string)
    role_attributes = "\n".join(attribute_strings)

  cf.write_json_file((role_attributes, custom_attributes), attributes_path)

  os.system("clear")


  return role_attributes, custom_attributes

def ner_role_script() -> str:

  role_attributes, custom_attributes = get_attributes()

  role_script = f"""You are a script supervisor compiling a list of characters in each scene. For the following selection, determine who are the characters, giving only their name and no other information. Please also determine the settings, both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, Kastea, Hell's Kitchen).{custom_attributes}.
If the scene is written in the first person, identify the narrator by their name. Ignore slash characters.
Be as brief as possible, using one or two words for each entry, and avoid descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris field of leftover asteroid pieces' should be 'Asteroid debris field'. ' Unmarked section of wall (potentially a hidden door)' should be 'unmarked wall section'
If you cannot find any mention of a specific attribute in the text, please respond with 'None found' on the same line as the attribute name. If you are unsure of a setting or no setting is shown in the text, please respond with 'None found' on the same line as the word 'Setting'
Please format the output exactly like this:
Characters:
character1
character2
character3
Setting:
Setting1 (interior)
Setting2 (exterior)
{role_attributes}"""


  return role_script

def search_names(chapters: list, folder_name: str, num_chapters: int, character_lists: list, character_lists_index: int) -> list:

  character_lists_path = f"{folder_name}/character_lists.json"
  
  role_script = ner_role_script()
  role_list = [role_script]
  
  model = "gpt-3.5-turbo-1106"
  max_tokens = 1000
  temperature = 0.2

  batched_chapters = cf.batch_list(chapters, role_list, model, max_tokens)

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|", position = 0, leave = True) as progress_bar:
    for batch in batched_chapters:
      
      first_chapter_number = batch[0][0] + 1
      last_chapter_number = batch[-1][0] + 1
      progress_bar.set_description(f"\033[92mProcessing batch of chapters: {first_chapter_number}-{last_chapter_number} of {num_chapters}", refresh = True)
      
      if batch[-1][0] < character_lists_index:
        progress_bar.update(len(batch))
        continue
 
      batched_prompts = [chapter for chapter_index, chapter in batch]
      batched_character_lists = cf.call_gpt_api(model, batched_prompts, role_script, temperature, max_tokens)

      for (chapter_index, _), character_list in zip(batch, batched_character_lists):
        chapter_number = chapter_index + 1
        chapter_tuple = (chapter_number, character_list)
        character_lists.append(chapter_tuple)
        cf.append_json_file(chapter_tuple, character_lists_path)

        progress_bar.update(1)

  os.system("clear")


  return character_lists

def character_analysis_role_script(attribute_table: dict, chapter_number: int) -> str:
  
  instructions = (
    'You are a developmental editor helping create a story bible. '
    'For each character in the chapter, note their appearance, personality, mood, relationships with other characters, '
    'known or apparent sexuality. Be detailed but concise.\n'
    'For each location in the chapter, note how the location is described, where it is in relation to other locations '
    'and whether the characters appear to be familiar or unfamiliar with the location. Be detailed but concise.\n'
    'If you cannot find any mention of a specific attribute in the text, please respond with "None found". '
    'If you are unsure of a setting or no setting is shown in the text, please respond with "None found". '
    'You will provide this information in the following JSON schema:'
  )

  chapter_data = attribute_table.get(chapter_number, {})
  characters = chapter_data.get("Characters", [])
  character_schema = {
    character_name: {
      "Appearance": "description", "Personality": "description", "Mood": "description", 
      "Relationships": "description", "Sexuality": "description"
    } for character_name in characters
  }

  other_attribute_schema = {
    key: {value: "description" for value in values}
    for key, values in chapter_data.items() if key != "Characters"
  }

  attributes_json = json.dumps({
    "characters": character_schema,
    **other_attribute_schema
  })
  
  role_script = f'{instructions}\n\n{attributes_json}'


  return role_script

def analyze_attributes(chapters: list, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary: dict, chapter_summary_index: int) -> dict:

  chapter_summary_path = f"{folder_name}/chapter_summary.json"

  role_list = []

  model = "gpt-4-1106-preview"
  max_tokens = 2000
  temperature = 0.4

  for i in num_chapters:
    role_script = character_analysis_role_script(attribute_table, i)
    role_list.append(role_script)

  batched_chapters = cf.batch_list(chapters, role_list, model, max_tokens)

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as progress_bar:
    for batch in batched_chapters:
                                   
      first_chapter_number = batch[0][0] + 1
      last_chapter_number = batch[-1][0] + 1
      progress_bar.set_description(f"\033[92mProcessing batch of chapters: {first_chapter_number}-{last_chapter_number} of {num_chapters}", refresh = True)

      if batch[-1][0] < chapter_summary_index:
        progress_bar.update(len(batch))
        continue

      batched_prompts = [chapter for chapter_index, chapter in batch]
      batched_role_scripts = [role_script for chapter_index, role_script in batch]

      batched_attribute_summaries = cf.call_gpt_api(model, batched_prompts, batched_role_scripts, temperature, max_tokens, response_type = "json")

      for (chapter_index, _), attribute_summary in zip(batch, batched_attribute_summaries):
        chapter_number = chapter_index + 1
        chapter_summary[chapter_number] = attribute_summary
        cf.append_json_file(chapter_summary, chapter_summary_path)
      
        progress_bar.update(1)

  os.system("clear")


  return chapter_summary


def analyze_book(user_folder: str, file_path: str):
  
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)

  sub_folder = os.path.basename(file_path).split('.')[0]
  folder_name = f"{user_folder}/{sub_folder}"
  os.makedirs(folder_name, exist_ok = True)


  #data_cleaning.data_cleaning(folder_name)
  #exit()
  # Prep work before doing the real work
  num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index = initialize_names(chapters, folder_name)

  # Named Entity Recognition  
  if character_lists_index < num_chapters:
    print(f"Starting character lists at chapter {character_lists_index + 1}")
    character_lists = search_names(chapters, folder_name, num_chapters, character_lists, character_lists_index)
  else:
    print("Character lists complete")
    character_lists = cf.read_json_file(f"{folder_name}/character_lists.json")

  attribute_table_path = os.path.join(folder_name, "attribute_table.json")
  if not os.path.exists(attribute_table_path):
    print("Building attribute table")
    attribute_table = sort_names(character_lists) 
    cf.write_json_file(attribute_table, attribute_table_path)
  else:
    print("Attribute table complete")
    attribute_table = cf.read_json_file(attribute_table_path)
  
  # Semantic search based on attributes pulled
  if chapter_summary_index < num_chapters:
    print(f"Starting chapter summaries at chapter {chapter_summary_index + 1}")
    chapter_summary = analyze_attributes(chapters, attribute_table, folder_name, num_chapters, chapter_summary, chapter_summary_index)

  # Cleaning data and preparing for presentation

  