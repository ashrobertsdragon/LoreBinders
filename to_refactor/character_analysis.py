import os
import time

from tqdm import tqdm
from typing import Tuple


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


def analyze_book(folder_name: str, chapters: list, narrator: str) -> str:

  start_time = time.time()

  # Prep work before doing the real work
  num_chapters, character_lists, character_lists_index, chapter_summary, chapter_summary_index, summaries, summaries_index = initialize_names(chapters, folder_name)

  # Named Entity Recognition  
  if character_lists_index < num_chapters:
    print(f"Starting character lists at chapter {character_lists_index + 1}")
    character_lists = search_names(chapters, folder_name, num_chapters, character_lists, character_lists_index)
  else:
    print("Character lists complete")
    character_lists = cf.read_json_file(os.path.join(folder_name, "character_lists.json"))

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
