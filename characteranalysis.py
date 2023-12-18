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
    f"If the scene is written in the first person, identify the narrator by their name.\n"
    f"Be as brief as possible, using one or two words for each entry, and avoid "
    f"descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris "
    f"field of leftover asteroid pieces' should be 'Asteroid debris field'. 'Unmarked "
    f"section of wall (potentially a hidden door)' should be 'unmarked wall section'\n"
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

  character_lists_path = f"{folder_name}/character_lists.json"

  role_script = ner_role_script()
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

def character_analysis_role_script(attribute_table: dict, chapter_number: int) -> str:

  instructions = (
    'You are a developmental editor helping create a story bible. '
    'For each character in the chapter, note their appearance, personality, '
    ' mood, relationships with other characters, known or apparent sexuality. '
    'Be detailed but concise.\n'
    'For each location in the chapter, note how the location is described, where '
    'it is in relation to other locations and whether the characters appear to be '
    'familiar or unfamiliar with the location. Be detailed but concise.\n'
    'If you cannot find any mention of a specific attribute in the text, please '
    'respond with "None found". '
    'If you are unsure of a setting or no setting is shown in the text, please '
    'respond with "None found".\n'
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
    "Characters": character_schema,
    **other_attribute_schema
  })

  role_script = f'{instructions}\n\n{attributes_json}'


  return role_script

def analyze_attributes(chapters: list, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary: dict, chapter_summary_index: int) -> dict:

  chapter_summary_path = f"{folder_name}/chapter_summary.json"

  role_list = []

  model = "gpt_four"
  max_tokens = 2000
  temperature = 0.4

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as progress_bar:
    for i, chapter in enumerate(chapters):
      if i < chapter_summary_index:
        continue
      chapter_number = i + 1
      progress_bar.set_description(f"\033[92mProcessing Chapter {i + 1}\033[0m", refresh = True)
      attribute_summary = ""

      role_script = character_analysis_role_script(attribute_table, chapter_number)
      prompt = f"Chapter Text: {chapter}"
      model = "gpt-4-1106-preview"

      attribute_summary = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type = "json")

      chapter_summary[chapter_number] = attribute_summary
      cf.append_json_file(chapter_summary, chapter_summary_path)

      progress_bar.update()

  cf.clear_screen()


  return chapter_summary

def summarize_attributes(folder_name: str) -> None:
  """
  Summarize the names for the attributes of the chapters in the folder.
  """

  prompt_list = []

  chapter_summaries_path = f"{folder_name}/chapter_summaries.json"
  chapter_summaries = cf.load_json_file(chapter_summaries_path)

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
        prompt_list.append(attribute, attribute_name, f"{attribute_name}: {description}")

  with tqdm(total = len(prompt_list), unit = "Prompt", ncols = 40) as progress_bar:
    for i, (attribute, attribute_name, prompt) in enumerate(prompt_list):
      progress_bar.set_description(f"\033[92mProcessing attriribute {i+1} of {len(prompt_list)}", refresh = True)      
      summary = cf.call_gpt_api(model_key, prompt, role_script, temperature, max_tokens)
      chapter_summaries[attribute][attribute_name]["summary"] = summary
      progress_bar.update(1)
  cf.append_json_file(chapter_summaries, chapter_summaries_path)

def analyze_book(user_folder: str, book_name: str):
  start_time = time.time()

  # Prep work before doing the real work
  file_path = f"{user_folder}/{book_name}"
  sub_folder = os.path.basename(file_path).split('.')[0]
  folder_name = f"{user_folder}/{sub_folder}"
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
    character_lists = cf.read_json_file(f"{folder_name}/character_lists.json")

  attribute_table_path = os.path.join(folder_name, "attribute_table.json")
  if not os.path.exists(attribute_table_path):
    print("Building attribute table")
    attribute_table = data_cleaning.sort_names(character_lists) 
    cf.write_json_file(attribute_table, attribute_table_path)
  else:
    print("Attribute table complete")
    attribute_table = cf.read_json_file(attribute_table_path)

  # Semantic search based on attributes pulled
  if chapter_summary_index < num_chapters:
    print(f"Starting chapter summaries at chapter {chapter_summary_index + 1}")
    chapter_summary = analyze_attributes(chapters, attribute_table, folder_name, num_chapters, chapter_summary, chapter_summary_index)

  # Cleaning data and preparing for presentation
  data_cleaning.data_cleaning(folder_name)
  summarize_attributes(folder_name)
  data_cleaning.final_reshape(folder_name)

  end_time = time.time()
  run_time = end_time - start_time
  cf.write_to_file(run_time, "run.txt")