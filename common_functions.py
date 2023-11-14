import json
import os
import re
import time
import traceback

from openai import OpenAI
from replit import db

TOKEN_CONVERSION_FACTOR = 0.7

if "tokens_used" not in db.keys():
  db["tokens_used"] = 0
if "minute" not in db.keys():
  db["minute"] = time.time()


def read_text_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = f.read()


    return read_file

  except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
    exit()

def read_json_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = json.load(f)

    
    return read_file
    
  except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
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

def check_continue():
  
  continue_program = ""

  while continue_program.upper() not in ["Y", "N"]:
    continue_program = input("If this looks right, type Y to continue the program. Type N to exit: ")

    if continue_program.upper() == "N":
      print("Exiting the program...")
      exit()
  
    elif continue_program.upper() != "Y":
      print("Invalid input. Please try again.")


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
  
  if retry_count == 3:
    exit()
  else:
    sleep_time = (5 - retry_count)  + (retry_count ** 2)
    print(f"Retry attempt #{retry_count} in {sleep_time} seconds.")
    time.sleep(sleep_time)

  
  return retry_count

def call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type = None, retry_count = 0, assistant_message = None):

  api_key = os.environ.get("OPENAI_API_KEY")
  if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")


    return

  client = OpenAI()

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

  if tokens_used + estimated_input_tokens + max_tokens > rate_limit:
    
    sleep_time = 60 - (call_start - minute)
    time.sleep(sleep_time)
    minute = time.time()
    
    tokens_used = 0
    db["minute"] = minute
    
  try:
    response = client.chat.completions.create(
      model = model,
      messages = messages,
      max_tokens = max_tokens,
      temperature = temperature,
      response_format = response_format
    )
    if response.choices and response.choices[0].message.content:
      content = response.choices[0].message.content.strip()
      tokens = response.usage.completion_tokens
      db["tokens_used"] = tokens_used + tokens
    else:
      raise Exception("No message content found")

  except Exception as e:
    retry_count = error_handle(e, retry_count)
    call_gpt_api(model, prompt, role_script, temperature, max_tokens, response_type, retry_count, assistant_message)

  if assistant_message:
    answer = assistant_message + content
  else:
    answer = content

  if response.choices[0].finish_reason == "length":

    assistant_message = answer
    call_gpt_api(model, prompt, role_script,  temperature, max_tokens = 500, response_type = response_type, assistant_message = assistant_message)
  
  
  return answer 
