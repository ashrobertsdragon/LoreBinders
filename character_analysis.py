import json
import os
import time

from tqdm import tqdm
from typing import Tuple

import common_functions as cf
from data_cleaning import data_cleaning, final_reshape, sort_names


ABSOLUTE_MAX_TOKENS = 4096
DEFAULT_ATTRIBUTES = ["Characters", "Settings"]

def initialize_names(chapters: list, folder_name: str) -> Tuple[int, list, int, dict, int, list, int]:

  num_chapters = len(chapters)
  print(f"\nTotal Chapters: {num_chapters} \n\n")

  character_lists_index = 0
  chapter_summary_index = 0
  summaries_index = 0
  character_lists_path = os.path.join(folder_name, "character_lists.json")
  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")
  summaries_path = os.path.join(folder_name, "summaries.json")

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

  if os.path.exists(summaries_path):
    summaries = cf.read_json_file(summaries_path)
    if not isinstance(summaries, list):
      summaries = []
  else:
    summaries = []
  summaries_index = len(summaries)

  return (
    num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index,
    summaries, summaries_index
  )


def character_analysis_role_script(attribute_table: dict, chapter_number: str) -> list:

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

  def generate_schema(attribute: str) -> str:

    if attribute == "Characters":
      schema_stub = {
        "Appearance": "description", "Personality": "description", "Mood": "description", 
        "Relationships": "description", "Sexuality": "description"
      }
    elif attribute == "Settings":
      schema_stub = {
        "Appearance": "description", "Relative location": "description", "Main character's familiarity": "description"
      }
    else:
      schema_stub = "description"

    schema = {name: schema_stub for name in chapter_data.get(attribute, [])}
    schema_json = json.dumps({attribute: schema})
    return schema_json

  def create_instructions(to_batch: list) -> str:

    instructions = (
      'You are a developmental editor helping create a story bible. \n'
      'Be detailed but concise, using short phrases instead of sentences. Do not '
      'justify your reasoning or provide commentary, only facts. Only one attribute '
      'per line, just like in the schema below, but all description for that '
      'attribute should be on the same line. If something appears to be '
      'miscatagorized, please put it under the correct attribute. USE ONLY STRINGS '
      'AND JSON OBJECTS, NO JSON ARRAYS. The output must be valid JSON.\n'
      'If you cannot find any mention of something in the text, please '
      'respond with "None found" as the description for that attribute. \n'
    )
    character_instructions = (
      'For each character in the chapter, describe their appearance, personality, '
      'mood, relationships to other characters, known or apparent sexuality.\n'
      'An example from an early chapter of Jane Eyre:\n'
      '"Jane Eyre": {"Appearance": "Average height, slender build, fair skin, '
      'dark brown hair, hazel eyes, plain apearance", "Personality": "Reserved, '
      'self-reliant, modest", "Mood": "Angry at her aunt about her treatment while '
      'at Gateshead", "Sexuality": "None found}'
    )
    setting_instructions = (
      'For each setting in the chapter, note how the setting is described, where '
      'it is in relation to other locations and whether the characters appear to be '
      'familiar or unfamiliar with the location. Be detailed but concise.\n'
      'If you are unsure of a setting or no setting is shown in the text, please '
      'respond with "None found" as the description for that setting.\n'
      'Here is an example from Wuthering Heights:\n'
      '"Moors": {"Appearance": Expansive, desolate, rugged, with high winds and '
      'cragy rocks", "Relative location": "Surrounds Wuthering Heights estate", '
      '"Main character\'s familiarity": "Very familiar, Catherine spent significant '
      'time roaming here as a child and represents freedom to her"}'
    )

    for attribute in to_batch:
      if attribute == "Characters":
        instructions += character_instructions
      if attribute == "Settings":
        instructions += setting_instructions
      else:
        other_attribute_list = [attr for attr in to_batch
                              if attr not in DEFAULT_ATTRIBUTES]
        instructions += (
          'Provide descriptons of ' +
          ', '.join(other_attribute_list) +
          ' without referencing specific characters or plot points\n')

    instructions += (
      'You will format this information as a JSON object using the folllowing schema '
      'where "description" is replaced with the actual information.\n'
    )
    return instructions

  def form_schema(to_batch: list) -> str:

    attributes_json = ""

    for attribute in to_batch:
      schema_json = generate_schema(attribute)
      attributes_json += schema_json

    return attributes_json
  
  def reset_variables(attribute: str, token_count: int) -> Tuple[list, int]:

    to_batch = [attribute]
    max_tokens = token_count
    return to_batch, max_tokens
  
  def append_attributes_batch(
      attributes_batch: list, to_batch: list, max_tokens: int, instructions: str
    ) -> list:
      
    attributes_json = form_schema(to_batch)
    attributes_batch.append((attributes_json, max_tokens, instructions))
    return attributes_batch
  
  for attribute, attribute_names in chapter_data.items():
    token_value = tokens_per.get(attribute, tokens_per["Other"])
    token_count = min(len(attribute_names) * token_value, ABSOLUTE_MAX_TOKENS)
    instructions =  create_instructions(to_batch)
    if max_tokens + token_count > ABSOLUTE_MAX_TOKENS:
      instructions =  create_instructions(to_batch)
      attributes_batch = append_attributes_batch(
          attributes_batch, to_batch, max_tokens, instructions
        )
      to_batch, max_tokens = reset_variables(attribute, token_count)
    else:
      to_batch.append(attribute)
      max_tokens += token_count

  if to_batch:
    instructions =  create_instructions(to_batch)
    attributes_batch = append_attributes_batch(
        attributes_batch, to_batch, max_tokens, instructions
      )

  for attributes_json, max_tokens, instructions in attributes_batch:
    role_script = (
      f'{instructions}'
      f'{attributes_json}'
    )
    role_script_info.append((role_script, max_tokens))
  return role_script_info

def analyze_attributes(chapters: list, attribute_table: dict, folder_name: str, num_chapters: int, chapter_summary: dict, chapter_summary_index: int) -> dict:

  chapter_summary_path = os.path.join(folder_name, "chapter_summary.json")
  model = "gpt_four"
  temperature = 0.4
  num_digits = len(str(num_chapters))

  with tqdm(total = num_chapters, unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as progress_bar:
    for i, chapter in enumerate(chapters):
      chapter_number = i + 1
      progress_bar.set_description(
        f"\033[92mProcessing Chapter {chapter_number:0{num_digits}d}", refresh = True
      )
      if i < chapter_summary_index:
        continue
      attribute_summary = ""
      attribute_summary_part = []
      attribute_summary_whole = []
      prompt = f"Chapter Text: {chapter}"
      role_script_info = character_analysis_role_script(attribute_table, str(chapter_number))
      progress_increment = 1 / len(role_script_info) if role_script_info else 1
      for role_script, max_tokens in role_script_info:
        attribute_summary_part = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type = "json")
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

  summaries_path = os.path.join(folder_name, "summaries.json")
  with_summaries_path = os.path.join(folder_name, "chapter_summaries_with.json")

  model_key = "gpt_three"
  temperature = 0.4
  max_tokens = 200
  role_script = "You are an expert summarizer. Please summarize the description over the course of the story for the following:"

  with tqdm(total = len(prompt_list), unit = "Summary", ncols = 40) as progress_bar:
    for i, (attribute, attribute_name, prompt) in enumerate(prompt_list):
      progress_bar.set_description(f"\033[92mProcessing attriribute {i+1} of {len(prompt_list)}", refresh = True)
      if i < summaries_index:
        progress_bar.update(1)
      summary = cf.call_gpt_api(model_key, prompt, role_script, temperature, max_tokens)
      summaries.append(summary)
      chapter_summaries[attribute][attribute_name]["summary"] = summary
      cf.append_json_file(summary, summaries_path)
      if os.path.exists(with_summaries_path):
        cf.append_json_file(chapter_summaries[attribute][attribute_name], with_summaries_path)
      else:
        cf.write_json_file(chapter_summaries, with_summaries_path)
      progress_bar.update(1)

  return chapter_summaries

def analyze_book(folder_name: str, chapters: list, narrator: str) -> str:

  start_time = time.time()

  # Prep work before doing the real work
  num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index, summaries, summaries_index = initialize_names(chapters, folder_name)

  attribute_table_path = os.path.join(folder_name, "attribute_table.json")
  if not cf.is_valid_json(attribute_table_path):
    print("Building attribute table")
    attribute_table = sort_names(character_lists, narrator) 
    cf.write_json_file(attribute_table, attribute_table_path)
  else:
    print("Attribute table complete")
    attribute_table = cf.read_json_file(attribute_table_path)

  # Semantic search based on attributes pulled
  if chapter_summary_index < num_chapters:
    print(f"Starting chapter summaries at chapter {chapter_summary_index + 1}")
    chapter_summary = analyze_attributes(chapters, attribute_table, folder_name, num_chapters, chapter_summary, chapter_summary_index)
  else:
    chapter_summary = cf.read_json_file(os.path.join(folder_name, "chapter_summary.json"))

  # Cleaning data and preparing for presentation
  chapter_summaries_path = os.path.join(folder_name, "chapter_summaries.json")
  if not cf.is_valid_json(chapter_summaries_path):
    cleaned_summaries = data_cleaning(folder_name, chapter_summary, narrator)
  else:
    cleaned_summaries = cf.read_json_file(chapter_summaries_path)

  prompt_list = create_summarization_prompts(cleaned_summaries)
  with_summaries_path = os.path.join(folder_name, "chapter_summaries_with.json")
  print(f"Index: {summaries_index} vs {len(prompt_list)}")
  if summaries_index < len(prompt_list):
    print(f"Generating summaries starting at {summaries_index}")
    with_summaries = summarize_attributes(cleaned_summaries, folder_name, summaries, summaries_index, prompt_list)
  else:
    with_summaries = cf.read_json_file(with_summaries_path)

  lorebinder_path = os.path.join(folder_name, "lorebinder.json")
  if not cf.is_valid_json(lorebinder_path):
    final_reshape(with_summaries, folder_name)

  end_time = time.time()
  run_time = end_time - start_time
  cf.write_to_file(str(run_time), "run.txt")
