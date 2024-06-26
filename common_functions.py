import logging
import json
import os
import re
import time
from typing import Any, Optional

import openai
import tiktoken
from openai import OpenAI

from data_cleaning import check_json, merge_json_halves
from error_handler import ErrorHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('api_calls.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.propagate = False

if not os.path.exists(".replit"):
  from dotenv import load_dotenv
  load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
  ErrorHandler.kill_app("OPENAI_API_KEY environment variable not set")

OPENAI_CLIENT = OpenAI()

def append_to_dict_list(dictionary, key, value):
  "Appends value to list of values in dictionary"

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
  "Opens and reads text file"

  try:
    with open(file_path, "r") as f:
      read_file = f.read()
    return read_file
  except FileNotFoundError:
    ErrorHandler.kill_app(f"Error: File '{file_path}' not found.")
  except PermissionError:
    ErrorHandler.kill_app(f"Error: Permission denied for {file_path}")

def read_json_file(file_path: str):
  "Opens and reads JSON file"

  try:
    with open(file_path, "r") as f:
      read_file = json.load(f)
    return read_file
  except Exception as e:
    ErrorHandler.kill_app(e)

def write_to_file(content, file_path):
  "Appends content to text file on new line"

  with open(file_path, "a") as f:
    f.write(content + "\n")

def separate_into_chapters(text: str) -> list:
  "Splits string at delimeter of three asterisks"

  return re.split("\s*\*\*\s*", text)

def write_json_file(content, file_path: str):
  "Writes JSON file"

  with open(file_path, "w") as f:
    json.dump(content, f, indent=2)

def append_json_file(content, file_path: str):
  "Reads JSON file, and adds content to datatype before overwriting"

  if os.path.exists(file_path):
    read_file = read_json_file(file_path)
  else:
    read_file = {} if isinstance(content, dict) else []
  if isinstance(read_file, list):
    read_file.append(content)
  elif isinstance(read_file, dict):
    read_file.update(content)
  write_json_file(read_file, file_path)

def is_valid_json(file_path: str) -> bool:
  "Checks to see if JSON file exists and is non-empty"

  if os.path.exists(file_path):
    return bool(read_json_file(file_path))
  return False

def check_continue():
  "Asks user to check output before continuing"

  continue_program = ""
  while continue_program.upper() not in ["Y", "N"]:
    continue_program = input("If this looks right, type Y to continue the program. Type N to exit: ")
    if continue_program.upper() == "N":
      print("Exiting the program...")
      logging.info("User exited the program...")
      exit(0)
    elif continue_program.upper() != "Y":
      print("Invalid input. Please try again.")
      logging.info("Invalid input. Please try again.")
    clear_screen()
  return

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
  "Counts tokens using OpenAI's tiktoken tokenizer"
  tokenizer = tiktoken.get_encoding("cl100k_base")
  return len(tokenizer.encode(text))

def error_handle(e: Any, retry_count: int) -> int:
  """
  Determines whether error is unresolvable or should be retried. If unresolvable,
  error is logged and administrator is emailed before exit. Otherwise, exponential
  backoff is used for up to 5 retries.

  Args:
    e: an Exception body
    retry_count: the number of attempts so far

  Returns:
    retry_count: the number of attemps so far
  """

  unresolvable_errors = [
    openai.BadRequestError,
    openai.AuthenticationError,
    openai.NotFoundError,
    openai.PermissionDeniedError,
    openai.UnprocessableEntityError
  ]

  error_code = getattr(e, "status_code", None)
  error_details = getattr(e, "response", {}).json().get("error", {})
  error_message = error_details.get("message", "Unknown error")

  if isinstance(e, tuple(unresolvable_errors)):
    ErrorHandler.kill_app(e)
  if error_code == 401:
    ErrorHandler.kill_app(e)
  if "exceeded your current quota" in error_message:
    ErrorHandler.kill_app(e)

  logging.exception(e)
  retry_count += 1
  if retry_count == 5:
    ErrorHandler.kill_app("Maximum retry count reached")
  else:
    sleep_time = (5 - retry_count)  + (retry_count ** 2)
    logging.warning(f"Retry attempt #{retry_count} in {sleep_time} seconds.")
    time.sleep(sleep_time)
  return retry_count

def call_gpt_api(model_key: str, prompt: str, role_script: str, temperature: float, max_tokens: int, response_type: Optional[str] = None, retry_count: Optional[int] = 0, assistant_message: Optional[str] = None) -> str:
  """
  Makes API calls to the OpenAI ChatCompletions engine.

  Args:
    model_key (str): The key of the GPT model to use.
    prompt (str): The user's prompt.
    role_script (str): The system's role script.
    temperature (float): The randomness of the generated text.
    max_tokens (int): The maximum number of tokens in the generated text.
    response_type (str, optional): The desired response format ("json" or "text"). Defaults to None.
    retry_count (int, optional): The number of retry attempts. Defaults to 0.
    assistant_message (str, optional): The assistant's message. Defaults to None.

  Returns:
    str: The generated content from the OpenAI GPT-3 model.
  """

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
      completion_tokens = response.usage.completion_tokens
      rate_limit_data["tokens_used"] += tokens
      write_json_file(rate_limit_data, "rate_limit_data.json")
    else:
      logging.error("No message content found")
      raise Exception("No message content found")

  except Exception as e:
    retry_count = error_handle(e, retry_count)
    content = call_gpt_api(model_key, prompt, role_script, temperature, max_tokens, response_type, retry_count, assistant_message)

  if assistant_message:
    if response_type == "json":
      new_part = content[1:]
      combined =  merge_json_halves(assistant_message, new_part)
      if combined:
        answer = combined
      else:
        answer = check_json(assistant_message + new_part)
    else:
      answer = assistant_message + content
  else:
    answer = content

  if response.choices[0].finish_reason == "length":
    length_warning = f"Max tokens exceeded.\nUsed {completion_tokens} of {max_tokens}"
    logging.warning(length_warning)
    print(length_warning)
    stub = f"original:\n{answer}\nLast complete:\n"
    if response_type == "json":
      last_complete = answer.rfind("},")
      assistant_message = answer[:last_complete + 1] if last_complete > 0 else ""
      debugging = stub + str(last_complete) if last_complete > 0 else f"{stub}Not found"
      write_to_file(debugging, "repair_log.txt")
    else:
      assistant_message = answer
    answer = call_gpt_api(model_key, prompt, role_script,  temperature, max_tokens = 500, response_type = response_type, assistant_message = assistant_message)
  return answer