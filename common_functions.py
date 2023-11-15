import logging
import json
import os
import re
import time

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


def write_to_file(content, file_path):
  
  with open(file_path, "a") as f:
    f.write(content + "\n")


  return

def separate_into_chapters(text):

  
  return re.split("\s*\*\*\s*", text)

def write_json_file(content, file_path):
  with open(file_path, "w") as f:
    json.dump(content, f, indent=2)


  return

def append_json_file(content, file_path):
  if os.path.exists(file_path):
      read_file = read_json_file(file_path)
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

  if os.path.exists("api_counter.json"):
    api_counter = read_json_file("api_counter.json")
  else:
    api_counter = {}
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

  messages = [
      {"role": "system", "content": role_script},
      {"role": "user", "content": prompt}
  ]

  if assistant_message:
    messages.append({
      "role": "assistant",
      "content": assistant_message
    })
    messages.append({
      "role": "user",
      "content": "Please continue from the exact point you left off without any commentary"
    })

  if response_type == "json":
    response_format = {"type": "json_object"}
  else:
    response_format = {"type": "text"}
  

  call_start = time.time()
  estimated_input_tokens = int((len(role_script) + len(prompt)) / TOKEN_CONVERSION_FACTOR)
  logging.info(f"Estimated input tokens: {estimated_input_tokens}")
  if model =="gpt-3.5-turbo-1106":
    append_to_dict_list(api_counter, "three_estimated_input_tokens", estimated_input_tokens)
  else:
    append_to_dict_list(api_counter, "four_estimated_input_tokens", estimated_input_tokens)

  if tokens_used + estimated_input_tokens + max_tokens > rate_limit:

    logging.warning("Rate limit exceeded")
    sleep_time = 60 - (call_start - minute)
    logging.info(f"Sleeping {sleep_time} seconds")
    print(f"Rate limit exceeded. Sleeping {sleep_time} seconds")
    time.sleep(sleep_time)
    minute = time.time()
    
    tokens_used = 0
    db["minute"] = minute

  try:
    if model == "gpt-3.5-turbo-1106":
      api_counter["three_api_count"] = api_counter.get("api_call_count", 0) + 1
    else:
      api_counter["four_api_count"] = api_counter.get("api_call_count", 0) + 1
    
    response = OPENAI_CLIENT.chat.completions.create(
      model = model,
      messages = messages,
      temperature = temperature,
      max_tokens = max_tokens,
      response_format = response_format,
      timeout = 90
    )
    
    if response.choices and response.choices[0].message.content:
      content = response.choices[0].message.content.strip()
      tokens = response.usage.total_tokens
      db["tokens_used"] = tokens_used + tokens
  
      tokens_completion = response.usage.completion_tokens
      tokens_prompt = response.usage.prompt_tokens

      if model == "gpt-3.5-turbo-1106":
        append_to_dict_list(api_counter, "three_prompt tokens", tokens_prompt)
        append_to_dict_list(api_counter, "three_completion tokens", tokens_completion)
      else:
        append_to_dict_list(api_counter, "four_prompt tokens", tokens_prompt)
        append_to_dict_list(api_counter, "four_completion tokens", tokens_completion)
    else:
      raise Exception("No message content found")
      logging.error("No message content found")

  except Exception as e:

    logging.exception(e)
    retry_count = error_handle(e, retry_count)
    call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type, retry_count, assistant_message)

  if assistant_message:
    answer = assistant_message + content
  else:
    answer = content

  if response.choices[0].finish_reason == "length":

    logging.warning("Max tokens exceeded")
    assistant_message = answer
    call_gpt_api(model, prompt, role_script,  temperature, max_tokens = 500, response_type = response_type, assistant_message = assistant_message)
  
  write_json_file(api_counter, "api_counter.json")
  
  
  return answer 
