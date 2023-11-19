import logging
import json
import os
import re
import time

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
TOKEN_CONVERSION_FACTOR = 0.7

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

def count_tokens(text):
  
  tokenizer = tiktoken.get_encoding("cl100k_base")


  return len(tokenizer.encode(text))

def error_handle(e, retry_count):
  
  retry_count += 1
  
  if retry_count == 5:
    logging.error("Maximum retry count reached")
    exit()
  else:
    sleep_time = (5 - retry_count)  + (retry_count ** 2)
    logging.warning(f"Retry attempt #{retry_count} in {sleep_time} seconds.")
    time.sleep(sleep_time)

  
  return retry_count

def call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type = None, retry_count = 0, assistant_message = None):

  tokens_used = db.get("tokens_used", 0)
  minute = db.get("minute", time.time())


  if time.time() - minute > 60:
    tokens_used = 0
    minute = time.time()
    db["minute"] = minute

  if model == "gpt-3.5-turbo-1106":
    rate_limit = 90000
  elif model == "gpt-4-1106-preview":
    rate_limit = 300000
  else:
    rate_limit = 250000

  input_tokens = count_tokens(prompt) + count_tokens(role_script)
  
  messages = [
      {"role": "system", "content": role_script},
      {"role": "user", "content": prompt}
  ]

  if assistant_message:
    added_prompt = "Please continue from the exact point you left off without any commentary"
    messages.append({
      "role": "assistant",
      "content": assistant_message
    })
    messages.append({
      "role": "user",
      "content": added_prompt
    })
    assistant_length = count_tokens(assistant_message) + count_tokens(added_prompt)
    input_tokens += assistant_length

  if response_type == "json":
    response_format = {"type": "json_object"}
  else:
    response_format = {"type": "text"}

  call_start = time.time()

  if tokens_used + input_tokens + max_tokens > rate_limit:

    logging.warning("Rate limit exceeded")
    sleep_time = 60 - (call_start - minute)
    logging.info(f"Sleeping {sleep_time} seconds")
    print(f"Rate limit exceeded. Sleeping {sleep_time} seconds")
    time.sleep(sleep_time)
    minute = time.time()
    
    tokens_used = 0
    db["minute"] = minute

  try:
    api_start = time.time()
    
    response = OPENAI_CLIENT.chat.completions.create(
      model = model,
      messages = messages,
      temperature = temperature,
      max_tokens = max_tokens,
      response_format = response_format,
      timeout = 90
    )
    api_end = time.time()
    api_run = api_end - api_start
    api_minute = api_run / 60
    api_sec = api_run % 60
    print(f"API Call Time: {api_minute} minutes and {api_sec} seconds")
    if response.choices and response.choices[0].message.content:
      content = response.choices[0].message.content.strip()
      tokens = response.usage.total_tokens
      db["tokens_used"] = tokens_used + tokens

    else:
      raise Exception("No message content found")
      logging.error("No message content found")

  except Exception as e:

    logging.exception(e)
    retry_count = error_handle(e, retry_count)
    call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type, retry_count, assistant_message)

  if assistant_message:
    answer = assistant_message + content
    print(answer)
    check_continue()
  else:
    answer = content

  if response.choices[0].finish_reason == "length":

    logging.warning("Max tokens exceeded")
    print("Max tokens exceeded:")
    print(answer)
    check_continue()
    assistant_message = answer
    call_gpt_api(model, prompt, role_script,  temperature, max_tokens = 500, response_type = response_type, assistant_message = assistant_message)

  
  return answer 
                 