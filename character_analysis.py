import os
import time

from tqdm import tqdm
from typing import Tuple

import common_functions as cf
from data_cleaning import data_cleaning, final_reshape


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


  # Prep work before doing the real work
  num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index, summaries, summaries_index = initialize_names(chapters, folder_name)

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
