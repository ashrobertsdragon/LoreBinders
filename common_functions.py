import logging
import json
import os
import re
import time

import tiktoken
from openai import OpenAI

logging.basicConfig(filename='api_calls.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

if not os.path.exists(".replit"):
  from dotenv import load_dotenv
  load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
  logging.error("OPENAI_API_KEY environment variable not set")
  raise Exception("OPENAI_API_KEY environment variable not set")

OPENAI_CLIENT = OpenAI()

def append_to_dict_list(dictionary, key, value):
  if key in dictionary:
      dictionary[key].append(value)
  else:
      dictionary[key] = [value]

def clear_screen():
  "Clears the the screen using OS-specific commands"
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def read_text_file(file_path: str):
  try:
    with open(file_path, "r") as f:
      read_file = f.read()
    return read_file
  except FileNotFoundError:
    logging.error(f"Error: File '{file_path}' not found.")
    exit()

def read_json_file(file_path: str):
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

def separate_into_chapters(text: str) -> list:
  return re.split("\s*\*\*\s*", text)

def write_json_file(content, file_path: str):
  with open(file_path, "w") as f:
    json.dump(content, f, indent=2)

def append_json_file(content, file_path: str):
  if os.path.exists(file_path):
    read_file = read_json_file(file_path)
  else:
    read_file = {} if isinstance(content, dict) else []
  if isinstance(read_file, list):
    read_file.append(content)
  elif isinstance(read_file, dict):
    read_file.update(content)
  write_json_file(read_file, file_path)

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
    clear_screen()
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

def call_gpt_api(model_key, prompt, role_script, temperature, max_tokens, response_type = None, retry_count = 0, assistant_message = None):
  rate_limit_data = read_json_file("rate_limit.json") if os.path.exists("rate_limit.json") else {}
  rate_limit_data["tokens_used"] = rate_limit_data.get("tokens_used", 0)
  rate_limit_data["minute"] = rate_limit_data.get("minute", time.time())
  if time.time() > rate_limit_data["minute"] + 60:
    rate_limit_data["minute"] = time.time()
  model_details = get_model_details(model_key)
  model_name = model_details["model_name"]
  rate_limit = is_rate_limit(model_key)
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

  if rate_limit_data["tokens_used"] + input_tokens + max_tokens > rate_limit:
    logging.warning("Rate limit exceeded")
    sleep_time = 60 - (time.time() - rate_limit_data["minute"])
    logging.info(f"Sleeping {sleep_time} seconds")
    print(f"Rate limit exceeded. Sleeping {sleep_time} seconds")
    time.sleep(sleep_time)    
    rate_limit_data["tokens_used"] = 0
    rate_limit_data["minute"] = time.time()
    write_json_file(rate_limit_data, "rate_limit_data.json")

  response_format = {"type": "json_object"} if response_type == "json" else {"type": "text"}

  try:
    api_start = time.time()
    response = OPENAI_CLIENT.chat.completions.create(
      model = model_name,
      messages = messages,
      temperature = temperature,
      max_tokens = max_tokens,
      response_format = response_format
    )
    api_end = time.time()
    api_run = api_end - api_start
    api_minute = api_run // 60
    api_sec = api_run % 60
    print(f"API Call Time: {api_minute} minutes and {api_sec:.2f} seconds")
    if response.choices and response.choices[0].message.content:
      content = response.choices[0].message.content.strip()
      tokens = response.usage.total_tokens
      rate_limit_data["tokens_used"]  += tokens
      write_json_file(rate_limit_data, "rate_limit_data.json")
    else:
      logging.error("No message content found")
      raise Exception("No message content found")

  except Exception as e:
    logging.exception(e)
    retry_count = error_handle(e, retry_count)
    call_gpt_api(model_key, prompt, role_script, temperature, max_tokens, response_type, retry_count, assistant_message)

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
    assistant_message = answer
    answer = call_gpt_api(model_key, prompt, role_script,  temperature, max_tokens = 500, response_type = response_type, assistant_message = assistant_message)
  return answer