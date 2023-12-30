import json
import os
import time

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
  else:
    character_lists = []
  character_lists_index = len(character_lists)

  if os.path.exists(chapter_summary_path):
    chapter_summary = cf.read_json_file(chapter_summary_path)
    if not isinstance(chapter_summary, dict):
      chapter_summary = {}
  else:
    chapter_summary = {}
  chapter_summary_index = len(chapter_summary)
  return num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index

def get_attributes(folder_name: str) -> Tuple[str, str]:

  dictionary_attributes_list = [] 
  attribute_strings = []
  attributes_path = os.path.join(folder_name, "attributes.json")
  if os.path.exists(attributes_path):
    role_attributes, custom_attributes = cf.read_json_file(attributes_path)
    return role_attributes, custom_attributes

  ask_attributes = input(
    "Besides characters and setting, what other attributes would you like ProsePal to "
    "search for (e.g. fantasy races, factions, religions, etc)? Please be as specific "
    "as possible. Attributes must be separated by commas for the program to work. "
    "Type N if you only want to search for characters and settings\n> "
  )

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
  cf.clear_screen()
  return role_attributes, custom_attributes

def ner_role_script(folder_name) -> str:

  role_attributes, custom_attributes = get_attributes(folder_name)
  role_script = (
    f"You are a script supervisor compiling a list of characters in each scene. "
    f"For the following selection, determine who are the characters, giving only "
    f"their name and no other information. Please also determine the settings, "
    f"both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, "
    f"Kastea, Hell's Kitchen).{custom_attributes}.\n"
    f"If the scene is written in the first person, try to identify the narrator by "
    f"their name. If you can't determine the narrator's identity. List 'Narrator' as "
    f"a character. Use characters' names instead of their relationship to the "
    f"narrator (e.g. 'Uncle Joe' should be 'Joe'. If the character is only identified "
    f"by their relationship to the narrator (e.g. 'Mom' or 'Grandfather'), list the "
    f"character by that identifier instead of the relationship (e.g. 'Mom' instead of "
    f"'Narrator's mom' or 'Grandfather' instead of 'Kalia's Grandfather'\n"
    f"Be as brief as possible, using one or two words for each entry, and avoid "
    f"descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris "
    f"field of leftover asteroid pieces' should be 'Asteroid debris field'. 'Unmarked "
    f"section of wall (potentially a hidden door)' should be 'unmarked wall section' "
    f"Do not use these examples unless they actually appear in the text.\n"
    f"If you cannot find any mention of a specific attribute in the text, please "
    f"respond with 'None found' on the same line as the attribute name. If you are "
    f"unsure of a setting or no setting is shown in the text, please respond with "
    f"'None found' on the same line as the word 'Setting'\n"
    f"Please format the output exactly like this:\n"
    f"Characters:\n"
    f"character1\n"
    f"character2\n"
    f"character3\n"
    f"Settings:\n"
    f"Setting1 (interior)\n"
    f"Setting2 (exterior)\n"
    f"{role_attributes}"
)
  return role_script

def search_names(chapters: list, folder_name: str, num_chapters: int, character_lists: list, character_lists_index: int) -> list:

  character_lists_path = os.path.join(folder_name, "character_lists.json")
  role_script = ner_role_script(folder_name)
  model = "gpt_three"
  max_tokens = 1000
  temperature = 0.2

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|", position = 0, leave = True) as progress_bar:
    for chapter_index, chapter in enumerate(chapters):
      progress_bar.set_description(f"\033[92mProcessing chapter {chapter_index + 1} of {num_chapters}", refresh = True)
      if chapter_index < character_lists_index:
        progress_bar.update(1)
        continue
      chapter_number = chapter_index + 1
      prompt = f"Text: {chapter}"
      character_list = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens)
      chapter_tuple = (chapter_number, character_list)
      character_lists.append(chapter_tuple)
      cf.append_json_file(chapter_tuple, character_lists_path)
      progress_bar.update(1)
  cf.clear_screen()
  return character_lists

def character_analysis_role_script(attribute_table: dict, chapter_number: str) -> list:

  absolute_max_tokens = 4096
  max_tokens = 0
  to_batch = []
  role_script_info = []
  attributes_batch = []
  attributes_json = ""

  tokens_per = {
    "Characters": 200,
    "Settings": 150,
    "Other": 100
  }

  chapter_data = attribute_table.get(chapter_number, {})

  character_schema = {
    character_name: {
      "Appearance": "description", "Personality": "description", "Mood": "description", 
      "Relationships": "description", "Sexuality": "description"
    } for character_name in chapter_data.get("Characters", [])
  }
  settings_schema = {
    setting_name: {
      "Relative location": "description", "Main character's familiarity": "description"
    } for setting_name in chapter_data.get("Settings", [])
  }
  other_attribute_schema = {
    key: {value: "description" for value in values} for key, values in 
    chapter_data.items() if key not in ["Characters", "Settings"]
  }

  def form_schema(to_batch, attributes_json):
    if "Characters" in to_batch:
      attributes_json += json.dumps({"Characters": character_schema})
    if "Settings" in to_batch:
      attributes_json += json.dumps({"Settings": settings_schema})
    for attr in to_batch:
      if attr not in ["Characters", "Settings"]:
        attributes_json += json.dumps({attr: other_attribute_schema[attr]})
    return attributes_json

  for attribute, attribute_names in chapter_data.items():
    token_value = tokens_per.get(attribute, tokens_per["Other"])
    token_count = min(len(attribute_names) * token_value, 4096)
    if max_tokens + token_count > absolute_max_tokens:
      attributes_json = form_schema(to_batch, attributes_json)
      attributes_batch.append((attributes_json, max_tokens))
      to_batch = [attribute]
      max_tokens = token_count
      attributes_json = ""
    else:
      to_batch.append(attribute)
      max_tokens += token_count

  if to_batch:
    attributes_json = form_schema(to_batch, attributes_json)
    attributes_batch.append((attributes_json, max_tokens))

  instructions = (
    f'You are a developmental editor helping create a story bible. \n'
    f'Be detailed but concise, using short phrases instead of sentences. Do not '
    f'justify your reasoning. Only one attribute per line, just like in the schema '
    f'below, but all description for that attribute should be on the same line. If '
    f'something appears to be miscatagorized, please put it under the correct '
    f'attribute.\n'
    f'For each character in the chapter, note their appearance, personality, '
    f'mood, relationships with other characters, known or apparent sexuality.\n'
    f'For each setting in the chapter, note how the setting is described, where '
    f'it is in relation to other locations and whether the characters appear to be '
    f'familiar or unfamiliar with the location. Be detailed but concise.\n'
    f'If you cannot find any mention of a specific attribute in the text, please '
    f'respond with "None found" as the description for that attribute. '
    f'If you are unsure of a setting or no setting is shown in the text, please '
    f'respond with "None found" as the description for that setting.\n'
  )

  for attributes_json, max_tokens in attributes_batch:
    if other_attribute_schema:
      other_attribute_list = [attr for attr in chapter_data 
                              if attr not in ["Characters", "Settings"]]
      other_attribute_instructions = ('Provide descriptons of ' +
                                      ', '.join(other_attribute_list) + ' without '
                                      ' referencing specific characters or plot points\n')
    else:
      other_attribute_instructions = ""

    role_script =(
      f'{instructions}'
      f'{other_attribute_instructions}'
      f'You will provide this information in the following JSON schema:'
      f'{attributes_json}'
    )
    role_script_info.append((role_script, max_tokens))
  return role_script_info 

def analyze_attributes(chapters: list, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary: dict, chapter_summary_index: int) -> dict:

  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")
  model = "gpt_four"
  temperature = 0.4
  roles = []
  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as progress_bar:
    for i, chapter in enumerate(chapters):
      if i < chapter_summary_index:
        continue
      chapter_number = i + 1
      progress_bar.set_description(f"\033[92mProcessing Chapter {i + 1}\033[0m", refresh = True)
      attribute_summary = ""
      attribute_summary_part = []
      attribute_summary_whole = []
      prompt = f"Chapter Text: {chapter}"
      role_script_info = character_analysis_role_script(attribute_table, str(chapter_number))
      roles.append((chapter_number, role_script_info))
      progress_increment = 1 /len(role_script_info)
      for role_script, max_tokens in role_script_info:
        attribute_summary_part = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type = "json")
        attribute_summary_whole.append(attribute_summary_part)
      progress_bar.update(progress_increment)
      attribute_summary = "{" + ",".join(part.lstrip("{").rstrip("}") for part in attribute_summary_whole) + "}"
      chapter_summary[chapter_number] = attribute_summary
      cf.append_json_file({chapter_number: attribute_summary}, chapter_summary_path)
      
  #cf.clear_screen()
  cf.append_json_file(roles, "role_scripts.json")
  return chapter_summary

def summarize_attributes(chapter_summaries: dict, folder_name: str) -> None:
  """
  Summarize the names for the attributes of the chapters in the folder.
  """

  prompt_list = []

  chapter_summaries_path = os.path.join(folder_name, "chapter_summaries.json")

  model_key = "gpt_three"
  temperature = 0.4
  max_tokens = 200
  role_script = f"You are an expert summarizer. Please summarize the description over the course of the story for the following:"

  for attribute, attribute_names in chapter_summaries.items():
    for attribute_name, chapters in attribute_names.items():
      for chapter, details in chapters.items():
        if attribute == "Characters" or attribute == "Settings":
          description = ", ".join(f"{trait}: {','.join(detail)}" for trait, detail in details.items())
        else:
          description = ", ".join(details)
        prompt_list.append((attribute, attribute_name, f"{attribute_name}: {description}"))

  with tqdm(total = len(prompt_list), unit = "Prompt", ncols = 40) as progress_bar:
    for i, (attribute, attribute_name, prompt) in enumerate(prompt_list):
      progress_bar.set_description(f"\033[92mProcessing attriribute {i+1} of {len(prompt_list)}", refresh = True)      
      summary = cf.call_gpt_api(model_key, prompt, role_script, temperature, max_tokens)
      chapter_summaries[attribute][attribute_name]["summary"] = summary
      progress_bar.update(1)
  cf.append_json_file(chapter_summaries, chapter_summaries_path)
  return chapter_summaries

def analyze_book(user_folder: str, book_name: str, narrator: str) -> str:

  start_time = time.time()

  # Prep work before doing the real work
  file_path = os.path.join(user_folder, book_name)
  sub_folder = os.path.basename(book_name).split('.')[0]
  folder_name = os.path.join(user_folder, sub_folder)
  os.makedirs(folder_name, exist_ok = True)
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)

  num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index = initialize_names(chapters, folder_name)

  # Named Entity Recognition  
  if character_lists_index < num_chapters:
    print(f"Starting character lists at chapter {character_lists_index + 1}")
    character_lists = search_names(chapters, folder_name, num_chapters, character_lists, character_lists_index)
  else:
    print("Character lists complete")
    character_lists = cf.read_json_file(os.path.join(folder_name, "character_lists.json"))

  attribute_table_path = os.path.join(folder_name, "attribute_table.json")
  if not os.path.exists(attribute_table_path):
    print("Building attribute table")
    attribute_table = data_cleaning.sort_names(character_lists, narrator) 
    cf.write_json_file(attribute_table, attribute_table_path)
  else:
    print("Attribute table complete")
    attribute_table = cf.read_json_file(attribute_table_path)

  # Semantic search based on attributes pulled
  if chapter_summary_index < num_chapters:
    print(len(attribute_table))
    print(f"Starting chapter summaries at chapter {chapter_summary_index + 1}")
    chapter_summary = analyze_attributes(chapters, attribute_table, folder_name, num_chapters, chapter_summary, chapter_summary_index)

  # Cleaning data and preparing for presentation
  chapter_summaries_path = os.path.join(folder_name, "chapter_summaries.json")
  if not os.path.exists(chapter_summaries_path):
    chapter_summaries = data_cleaning.data_cleaning(folder_name)
  else:
    chapter_summaries = cf.read_json_file(chapter_summaries_path)
  with_summaries_path = os.path.join(folder_name, "chapter_summaries_with.json")
  if not os.path.exists(with_summaries_path):
    with_summaries = summarize_attributes(chapter_summaries, folder_name)
  else:
    with_summaries = cf.read_json_file(with_summaries_path)
  data_cleaning.final_reshape(with_summaries, folder_name)

  end_time = time.time()
  run_time = end_time - start_time
  cf.write_to_file(str(run_time), "run.txt")
  return folder_name