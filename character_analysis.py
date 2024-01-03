import json
import os
import time

from tqdm import tqdm
from typing import Tuple
import common_functions as cf
from data_cleaning import data_cleaning, final_reshape


ABSOLUTE_MAX_TOKENS = 4096
DEFAULT_ATTRIBUTES = ["Characters", "Settings"]

def initialize_names(chapters: list, folder_name: str) -> Tuple[int, list, int, dict, int, dict, int]:

  num_chapters = len(chapters)
  print(f"\nTotal Chapters: {num_chapters} \n\n")

  character_lists_index = 0
  chapter_sumamary_paragraphs_index = 0
  chapter_summary_index = 0
  summaries_index = 0
  character_lists_path = os.path.join(folder_name, "character_lists.json")
  chapter_summary_paragraphs_path = os.path.join(folder_name, "chapter_summary_paragraphs.json")
  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")
  summaries_path = os.path.join(folder_name, "summaries.json")

  if os.path.exists(character_lists_path):
    character_lists =  cf.read_json_file(character_lists_path)
    if not isinstance(character_lists, list):
      character_lists = []
  else:
    character_lists = []
  character_lists_index = len(character_lists)

  if os.path.exists(chapter_summary_paragraphs_path):
    chapter_summary_paragraphs = cf.read_json_file(chapter_summary_paragraphs_path)
    if not isinstance(chapter_summary_paragraphs, dict):
      chapter_summary = {}
  else:
    chapter_summary = {}
  chapter_sumamary_paragraphs_index = len(chapter_summary_paragraphs)

  if os.path.exists(chapter_summary_path):
    chapter_summary = cf.read_json_file(chapter_summary_path)
    if not isinstance(chapter_summary, dict):
      chapter_summary = {}
  else:
    chapter_summary = {}
  chapter_summary_index = len(chapter_summary)

  if os.path.exists(summaries_path):
    summaries = cf.read_json_file(summaries_path)
    if not isinstance(summaries, list):
      summaries = []
  else:
    summaries = []
  summaries_index = len(summaries)

  return (
    num_chapters, character_lists, character_lists_index, chapter_summary_paragraphs,
    chapter_sumamary_paragraphs_index, chapter_summary, chapter_summary_index,
    summaries, summaries_index
  )

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
  
  max_tokens = 0
  tokens_per = 200
  attr_list = []
  other_attribute_list = []
  role_batch = []

  chapter_data = attribute_table.get(chapter_number, {})
  attributes_list = [(attribute, f"{attribute}: ', '.join({names})")
                    for attribute, names in chapter_data.items()]

  def create_script(attr_list: list, role_batch: list, max_tokens: int) -> str:

    instructions = (
      f'You are a developmental editor helping create a story bible. For each of '
      f'the below write 1-2 paragraphs.\n'
      f'For each character in the chapter, note their appearance, personality, '
      f'mood, relationships with other characters, known or apparent sexuality.\n'
      f'For each setting in the chapter, note how the setting is described, where '
      f'it is in relation to other locations and whether the characters appear to be '
      f'familiar or unfamiliar with the location. Be detailed but concise.\n'
    )
    if any(attr not in DEFAULT_ATTRIBUTES for attr in attr_list):
      instructions += (
        'Provide descriptons of ' +
        ', '.join(names for attribute, names in chapter_data.items()
                  if attribute in attr_list and attribute not in DEFAULT_ATTRIBUTES) +
        ' without referencing specific characters or plot points\n'
      )
    role_script = instructions  + "\n".join(attribute_str for _, attribute_str in attr_list)
    role_batch.append((role_script, max_tokens))
    return role_batch

  for attribute, attribute_str in attributes_list:
    token_count = min(len(chapter_data[attribute]) * tokens_per, ABSOLUTE_MAX_TOKENS)
    if max_tokens + token_count > ABSOLUTE_MAX_TOKENS:
      role_batch = create_script(other_attribute_list, attr_list, role_batch, max_tokens)
      max_tokens = token_count
      attr_list = [attribute. attribute_str]
    else:
      max_tokens += token_count
      attr_list.append(attribute, attribute_str)

  if attr_list:
    role_batch = create_script(other_attribute_list, attr_list, role_batch, max_tokens)
  return role_batch

def analyze_attributes(chapters: list, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary_paragraphs: dict, chapter_summary_index: int) -> dict:

  chapter_summary_paragraphs_path = os.path.join(folder_name, "chapter_summary_paragraphs.json")
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
      progress_increment = 1 /len(role_script_info)
      for role_script, max_tokens in role_script_info:
        attribute_summary_part = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens)
        attribute_summary_whole.append(attribute_summary_part)
      progress_bar.update(progress_increment)
      attribute_summary = "\n".join(part for part in attribute_summary_whole)
      chapter_summary_paragraphs[chapter_number] = attribute_summary
      cf.append_json_file({chapter_number: attribute_summary}, chapter_summary_paragraphs_path)
      
  cf.clear_screen()
  return chapter_summary_paragraphs

def json_formatting_role_script(attribute_table: dict, chapter_number: str, paragraphs: str, model_key: str) -> list:

  max_tokens = 0
  attributes_batch = []
  to_batch = []
  role_script_info = []

  tokens_per = {
    "Characters": 200,
    "Settings": 150,
    "Other": 100
  }

  chapter_data = attribute_table.get(chapter_number, {})
  context_window = cf.get_model_details(model_key)["context_window"]
  prompt_length = cf.count_tokens(paragraphs)

  def generate_schema_and_tokens(attribute: str) -> Tuple(str, int):

    if attribute == "Characters":
      schema_stub = {
        "Appearance": "description", "Personality": "description", "Mood": "description", 
        "Relationships": "description", "Sexuality": "description"
      }
    elif attribute == "Settings":
      schema_stub = {
        "Relative location": "description", "Main character's familiarity": "description"
      }
    else:
      schema_stub = "description"

    schema = {name: schema_stub for name in chapter_data.get(attribute, [])}
    schema_json = json.dumps({attribute: schema})
    schema_tokens = cf.count_tokens(schema_json)
    return schema_json, schema_tokens

  def create_instructions(to_batch: list) -> Tuple(str, int):

    instructions = (
      f'You are an expert JSON formatter. Please take the text below and output it '
      f'as JSON using the schema below.\n'
      f'Be detailed but concise, using short phrases instead of sentences. Do not '
      f'justify your reasoning. Only one attribute per line, just like in the schema '
      f'below, but all description for that attribute should be on the same line. If '
      f'something appears to be miscatagorized, please put it under the correct '
      f'attribute.\n'
    )

    if any(attribute not in DEFAULT_ATTRIBUTES for attribute in to_batch):
      other_attribute_list = [attr for attr in to_batch
                            if attr not in DEFAULT_ATTRIBUTES]
      instructions += (
        'Provide descriptons of ' +
        ', '.join(other_attribute_list) +
        ' without referencing specific characters or plot points\n')

    instructions += "You will provide this information in the following JSON schema:"
    instruction_tokens = cf.count_tokens(instructions)
    return instructions, instruction_tokens

  def form_schema(to_batch: list) -> Tuple(str, int):

    attributes_json = ""
    schema_token_count = 0

    for attribute in to_batch:
      schema_json, schema_tokens = generate_schema_and_tokens(attribute)
      attributes_json += schema_json
      schema_token_count += schema_tokens

    return attributes_json, schema_token_count
  
  def exceeds_context_window(max_tokens: int, token_count: int, schema_token_count: int, instructions_tokens: int) -> bool:

    return max_tokens + token_count + schema_token_count + instructions_tokens + prompt_length > context_window
  
  def reset_variables(attribute: str, token_count: int) -> Tuple(list, int):

    to_batch = [attribute]
    max_tokens = token_count
    return to_batch, max_tokens
  
  def append_attributes_batch(attributes_batch, to_batch, max_tokens, instructions):
      
    attributes_json, schema_token_count = form_schema(to_batch)
    attributes_batch.append((attributes_json, max_tokens, instructions))
    return attributes_batch, schema_token_count
  
  for attribute, attribute_names in chapter_data.items():
    token_value = tokens_per.get(attribute, tokens_per["Other"])
    token_count = min(len(attribute_names) * token_value, ABSOLUTE_MAX_TOKENS)
    instructions, instructions_tokens =  create_instructions(to_batch)
    if max_tokens + token_count > ABSOLUTE_MAX_TOKENS:
      attributes_batch, schema_token_count = append_attributes_batch(attributes_batch, to_batch, max_tokens, instructions)
      to_batch, max_tokens = reset_variables(attribute, token_count)
    elif exceeds_context_window(max_tokens, token_count, schema_token_count, instructions_tokens):
      attributes_batch, schema_token_count = append_attributes_batch(attributes_batch, to_batch[:-1], max_tokens, instructions)
      to_batch, max_tokens = reset_variables(attribute, token_count)
    else:
      to_batch.append(attribute)
      max_tokens += token_count

  if to_batch:
    attributes_json, schema_token_count = form_schema(to_batch)
    if exceeds_context_window(max_tokens, token_count, schema_token_count, instructions_tokens):
      remove_last_attribute = to_batch.pop()
      attributes_batch, schema_token_count = append_attributes_batch(attributes_batch, remove_last_attribute, max_tokens, instructions)
      to_batch, max_tokens = reset_variables(to_batch, token_count)
      attributes_json, schema_token_count = form_schema(to_batch)
    attributes_batch.append((attributes_json, max_tokens, instructions))

  for attributes_json, max_tokens, instructions in attributes_batch:
    role_script = (
      f'{instructions}'
      f'{attributes_json}'
    )
    role_script_info.append((role_script, max_tokens))

  return role_script_info

def form_json(chapter_summary_paragraphs: dict, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary: dict, chapter_summary_index: int) -> dict:

  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")
  model = "gpt_three"
  temperature = 0.2

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as progress_bar:
    for i, paragraphs in enumerate(chapter_summary_paragraphs):
      if i < chapter_summary_index:
        continue
      chapter_number = i + 1
      progress_bar.set_description(f"\033[92mProcessing Chapter {chapter_number}\033[0m", refresh = True)
      attribute_summary = ""
      attribute_summary_part = []
      attribute_summary_whole = []
      prompt = f"Information to add to JSON: {paragraphs}"
      role_script_tuple = json_formatting_role_script(attribute_table, str(chapter_number), paragraphs, model)
      progress_increment = 1 /len(role_script_tuple)
      for role_script, max_tokens in role_script_tuple:
        attribute_summary_part = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_ = "json")
        attribute_summary_whole.append(attribute_summary_part)
      progress_bar.update(progress_increment)
      attribute_summary = "{" + ",".join(part.lstrip("{").rstrip("}") for part in attribute_summary_whole) + "}"
      chapter_summary[chapter_number] = attribute_summary
      cf.append_json_file({chapter_number: attribute_summary}, chapter_summary_path)
      
  cf.clear_screen()
  return chapter_summary

def create_summarization_prompts(chapter_summaries: dict) -> tuple:

  prompt_list = []
  for attribute, attribute_names in chapter_summaries.items():
    for attribute_name, chapters in attribute_names.items():
      for _, details in chapters.items():
        if attribute in DEFAULT_ATTRIBUTES:
          description = ", ".join(f"{trait}: {','.join(detail)}" for trait, detail in details.items())
        else:
          description = ", ".join(details)
        prompt_list.append((attribute, attribute_name, f"{attribute_name}: {description}"))
  return prompt_list

def summarize_attributes(chapter_summaries: dict, folder_name: str, summaries: list, summaries_index: int, prompt_list: tuple) -> dict:
  """
  Summarize the names for the attributes of the chapters in the folder.
  """

  prompt_list = []

  summaries_path = os.path.join(folder_name, "summaries.json")
  with_summaries_path = os.path.join(folder_name, "chapter_summaries_with.json")

  model_key = "gpt_three"
  temperature = 0.4
  max_tokens = 200
  role_script = f"You are an expert summarizer. Please summarize the description over the course of the story for the following:"

  with tqdm(total = len(prompt_list), unit = "Summary", ncols = 40) as progress_bar:
    for i, (attribute, attribute_name, prompt) in enumerate(prompt_list):
      progress_bar.set_description(f"\033[92mProcessing attriribute {i+1} of {len(prompt_list)}", refresh = True)
      if i < summaries_index:
        progress_bar.update(1)
      summary = cf.call_gpt_api(model_key, prompt, role_script, temperature, max_tokens)
      summaries.append(summary)
      chapter_summaries[attribute][attribute_name]["summary"] = summary
      cf.append_json_file(summary, summaries_path)
      cf.append_json_file(chapter_summaries[attribute][attribute_name]["summary"], with_summaries_path)
      progress_bar.update(1)

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

  num_chapters, character_lists, character_lists_index, chapter_summary_paragraphs, chapter_summary_paragraphs_index, chapter_summary, chapter_summary_index, summaries, summaries_index = initialize_names(chapters, folder_name)

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
  if chapter_summary_paragraphs_index < num_chapters:
    print(f"Starting chapter summary paragraphs at chapter {chapter_summary_index + 1}")
    chapter_summary_paragraphs = analyze_attributes(chapters, attribute_table, folder_name, num_chapters, chapter_summary_paragraphs, chapter_summary_paragraphs_index)
  else:
    print("Chapter summary paragraphs written")
    chapter_summary_paragraphs = cf.read_json_file(os.path.join(folder_name, "chapter_summary_paragraphs.json"))
  
  # Form JSON for chapter summaries
  if chapter_summary_index < num_chapters:
    print(f"Starting JSON formation of chapter summaries at chapter {chapter_summary_index + 1}")
    chapter_summary = form_json(chapter_summary_paragraphs, attribute_table, folder_name, num_chapters, chapter_summary, chapter_summary_index)
  else:
    chapter_summary = cf.read_json_file(os.path.join(folder_name, "chapter_summary.json"))

  # Cleaning data and preparing for presentation
  chapter_summaries_path = os.path.join(folder_name, "chapter_summaries.json")
  if not os.path.exists(chapter_summaries_path):
    cleaned_summaries = data_cleaning(folder_name, chapter_summary)
  else:
    cleaned_summaries = cf.read_json_file(chapter_summaries_path)

  prompt_list = create_summarization_prompts(cleaned_summaries)
  with_summaries_path = os.path.join(folder_name, "chapter_summaries_with.json")
  if summaries_index < len(prompt_list):
    print(f"Generating summaries starting at {summaries_index}")
    with_summaries = summarize_attributes(cleaned_summaries, folder_name, summaries, summaries_index, prompt_list)
  else:
    with_summaries = cf.read_json_file(with_summaries_path)

  lorebinder_path = os.path.join(folder_name, "lorebinder.json")
  if not os.path.exists(lorebinder_path):
    final_reshape(with_summaries, folder_name)

  end_time = time.time()
  run_time = end_time - start_time
  cf.write_to_file(str(run_time), "run.txt")
  return folder_name