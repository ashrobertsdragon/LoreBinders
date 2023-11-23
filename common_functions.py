import logging
import json
import os
import re
import time
from typing import List, Optional

import tiktoken
from openai import OpenAI
from replit import db


logging.basicConfig(filename='api_calls.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
  raise Exception("OPENAI_API_KEY environment variable not set")
  logging.exception("OPENAI_API_KEY environment variable not set")

OPENAI_CLIENT = OpenAI()

if "tokens_used" not in db.keys():
  db["tokens_used"] = 0
if "minute" not in db.keys():
  db["minute"] = time.time()

def append_to_dict_list(dictionary, key, value):
  if key in dictionary:
      dictionary[key].append(value)
  else:
      dictionary[key] = [value]


def read_text_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = f.read()


    return read_file

  except FileNotFoundError:
    logging.error(f"Error: File '{file_path}' not found.")
    exit()

def read_json_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = json.load(f)

    
    return read_file
    
  except FileNotFoundError:
    logging.error(f"Error: File '{file_path}' not found.")
    exit()

  except json.decoder.JSONDecodeError:
    logging.error(f"Error: File '{file_path}' not valid JSON.")
    exit()

  except Exception as e:
    logging.error(f"Error: {e}")
    exit()


def write_to_file(content, file_path):
  
  with open(file_path, "a") as f:
    f.write(content + "\n")


  return

def separate_into_chapters(text):

  
  return re.split("\s*\*\*\s*", text)

def write_json_file(content, file_path: str):
  with open(file_path, "w") as f:
    json.dump(content, f, indent=2)


  return

def append_json_file(content, file_path: str):
  if os.path.exists(file_path):
      read_file = read_json_file(file_path)
      print(f"{file_path} exists")
  else:
      read_file = [] if isinstance(content, list) else {}

  if isinstance(read_file, list):
      read_file.append(content)
  elif isinstance(read_file, dict) and isinstance(content, dict):
      read_file.update(content)

  write_json_file(read_file, file_path)


  return


def check_continue():
  
  continue_program = ""

  while continue_program.upper() not in ["Y", "N"]:
    continue_program = input("If this looks right, type Y to continue the program. Type N to exit: ")

    if continue_program.upper() == "N":
      print("Exiting the program...")
      logging.info("User exited the program...")
      exit()
  
    elif continue_program.upper() != "Y":
      print("Invalid input. Please try again.")
      logging.info("Invalid input. Please try again.")

    os.system("clear")


  return

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

def get_model_details(model_key: str) -> dict:
  """
  Interprets the generic model key and returns model-specific details.
  """
  
  model_details = {
    "gpt_three": {
      "model_name": "gpt-3.5-turbo-1106",
      "rate_limit": 90000,
        "context_window": 16000
    },
    "gpt_four": {
      "model_name": "gpt-4-1106-preview",
      "rate_limit": 300000,
        "context_window": 128000
    }
}


  return model_details.get(model_key, {"model_name": None, "rate_limit": 250000, "context_window": 4096})

def is_rate_limit(model_key: str) -> int:
  """
  Returns the rate limit based on the model key.
  """
  
  model_details = get_model_details(model_key)

  
  return model_details["rate_limit"]



def count_tokens(text):
  
  tokenizer = tiktoken.get_encoding("cl100k_base")


  return len(tokenizer.encode(text))

def batch_count(chapters: list, role_list: list, model_key: str, max_tokens: int) -> list:
  """
  Batches the chapters based on token counts and model-specific details.
  """

  token_count = 0
  batch_limit = 20
  batched = []
  batched_chapters = []

  model_details = get_model_details(model_key)
  context_window = model_details["context_window"]
  rate_limit = is_rate_limit(model_key) - db["tokens_used"]

  for chapter_index, (chapter, role_script) in enumerate(zip(chapters, role_list):
    chapter_token_count = count_tokens(chapter)
    role_count = count_tokens(role_script)
    token_count += chapter_token_count
    total_tokens = token_count + role_count + max_tokens
    if total_tokens < context_window and total_tokens < rate_limit and len(batched_chapters < batch_limit):
      batch.append((chapter_index, chapter))
    else:
      if batched:
        batched_chapters.append(chapter)
      batched = [(chapter_index, chapter)]
      token_count = chapter_token_count

  if batched:
    batched_chapters.append(chapter)

  
  return batched_chapters

def error_handle(e, retry_count: int) -> int:
  
  logging.error(e)
  max_retries = 10 if e == "missing entries in batched_contents" else 5
  
  
  retry_count += 1
  
  if retry_count >= max_retries:
    logging.error("Maximum retry count reached")
    exit()
  else:
    sleep_time = (5 - retry_count)  + (retry_count ** 2)
    logging.warning(f"Retry attempt #{retry_count} in {sleep_time} seconds.")
    time.sleep(sleep_time)

  
  return retry_count

def call_gpt_api(model: str, batched_prompts: List[int], batched_role_scripts: List[str], temperature: float, max_tokens: int, response_type: Optional[str] = None, retry_count: int = 0):
  """
  Calls the GPT API with the provided parameters.
  """
  
  model_details = get_model_details(model_key)
  model_name = model_details["model_name"]

  input_tokens = sum(count_tokens(prompt) + count_tokens(role_script) for prompt, role_script in batched_prompts, batched_role_scripts in zip(batched_prompts, batched_role_scripts))

  message_batch = [
    [
      {"role": "system", "content": role_script},
      {"role": "user", "content": prompt}
    ] for prompt, role_script in zip(prompts, role_scripts)]

  timeout = len(message_batch) * 90 # 90 seconds per prompt

  tokens_used = db.get("tokens_used", 0)
  minute = db.get("minute", time.time())

  if time.time() - minute > 60:
    tokens_used = 0
    minute = time.time()
    db["tokens_used"] = tokens_used
    db["minute"] = minute


  rate_limit = is_rate_limit(model)
  if tokens_used + input_tokens + max_tokens > rate_limit:
    logging.warning("Rate limit exceeded")
    sleep_time = 60 - (time.time() - minute)
    logging.info(f"Sleeping {sleep_time} seconds")
    print(f"Rate limit exceeded. Sleeping {sleep_time} seconds")

    tokens_used = 0
    minute = time.time()
    db["tokens_used"] = tokens_used
    db["minute"] = minute

  response_format = {"type": "json_object"} if response_type == "json": else {"type": "text"}

  try:
    api_start = time.time()
    
    responses = OPENAI_CLIENT.chat.completions.create(
      model = model_name,
      messages = messages_batch,
      temperature = temperature,
      max_tokens = max_tokens,
      response_format = response_format,
      timeout = timeout
    )
    api_end = time.time()
    api_run = api_end - api_start
    api_minute = api_run // 60
    api_sec = api_run % 60
    print(f"API Call Time: {api_minute} minutes and {api_sec} seconds")

    batched_contents = [None] * len(batched_prompts)
    error_list, retry_indices = [], []
    total_tokens = 0

    if responses.choices:
      for index, choice in enumerate(responses.choices):
        if choice.finish_reason == "length":
          error_message = f"Response length exceeded the maximum length for prompt {index}"
          error_list.append(error_message)
          total_tokens += response.usage.total_tokens          
          retry_indices.append[index]

        elif choice.message and choice.message.content:
          content = choice.message.content.strip()
          total_tokens += response.usage.total_tokens
          batched_contents[index] = content

        else:
          error_message = f"No response for prompt {index}"
          error_list.append(error_message)     
          retry_indicies.append(index)


      db["tokens_used"] += total_tokens
      
      if retry_indicies:
        retry_prompts = [batched_prompts[i] for i in retry_indices]
        retry_role_scripts = [batched_role_scripts[i] for i in retry_indices]
        
        e = ", ".join(error_list)
        
        logging.warning(f"Retrying prompts indices: {retry_indicies}. Errors: {e}"
        retry_count = error_handle(e, retry_count) 
        
        batched_retries = call_gpt_api(model, bad_response_prompts, bad_response_role_scripts, temperature, max_tokens, response_type, retry_count)

        for retry_index, retry_content in zip(retry_indices, batched_retries):
          batched_contents[retry_index] = retry_content
          
      else:


        return batched_contents
          
    else:
      raise Exception("No message content found")

  except Exception as e:

    logging.exception(e)
    retry_count = error_handle(e, retry_count)
    batched_retries = call_gpt_api(model, bad_response_prompts, bad_response_role_scripts, temperature, max_tokens, response_type, retry_count)
    
    for retry_index, retry_content in zip(retry_indices, batched_retries):
      batched_contents[retry_index] = retry_content

  
  return batched_contents
    