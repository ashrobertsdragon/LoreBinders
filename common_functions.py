import os
import re
import time
import traceback
import openai
import json
from replit import db

if "tokens_used" not in db.keys():
  db["tokens_used"] = 0
if "minute_start_time" not in db.keys():
  db["minute_start_time"] = time.time()

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

def read_state(folder_name):
  
  # Check to see if the state was saved, meaning the API timed out
  state = {}
  state_file = f"{folder_name}/state.json"
  if os.path.exists(state_file):
    with open(state_file, "r") as f:
      state = json.load(f)

  
  return state

def remove_state_file(folder_name):
  
  state_file = f"{folder_name}/state.json"
  if os.path.exists(state_file):
    os.remove(state_file)


  return

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

def save_state_to_file(state, kwargs):
  state_file = f"{folder_name}/state.json"
  status = [state, kwargs]
  
  with open(state_file, "w") as f:
    json.dump(status, f)


  return

def check_continue():
  
  # Ask if ready to continue
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

def error_handle(e, retry_count, state, **kwargs):
  
  # Initialize retry variables
  max_retries = 3
  print(f"\nAn exception occurred: {e}")
  # Increment the retry count
  retry_count += 1

  if retry_count < max_retries:  # Retry
    print("Retrying in 5 seconds...")
    time.sleep(5)

  else:  #Save sate & exit
    print("Max retry limit reached. Saving Progress & exiting...")
    traceback.print_exc()
    save_state_to_file(state, kwargs)
    exit()

  
  return retry_count

def call_gpt_api(model, prompt, role_char, temperature, max_tokens, assistant_message = None):

  api_key = os.environ.get("OPENAI_API_KEY")
  if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")


    return

  tokens_used = db.get('tokens_used', 0)
  minute = db.get('minute', time.time())

  if model == "gpt-3.5-turbo":
    rate_limit = 90000
  elif model == "gpt-3.5-turbo-16k":
    rate_limit = 180000
  elif model == "gpt-4":
    rate_limit = 10000
  else:
    rate_limit = 250000

  messages = [
      {"role": "system", "content": role_char},
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

  call_start = time.time()
  input_tokens = (len(role_char) + len(prompt)) / 0.7 # estimate token length

  if tokens_used + input_tokens + max_tokens > rate_limit:
    sleep_time = 60 - (call_start - minute)
    time.sleep(sleep_time)
    
    tokens_used = 0
    minute = time.time()

    db["tokens_used"] = tokens_used
    db["minute"] = minute
    
  response = openai.ChatCompletion.create(
    model = model,
    messages = messages,
    max_tokens = max_tokens,
    api_key = api_key,
    temperature = temperature
  )

  answer = response.choices[0].message['content'].strip()

  tokens_used = input_tokens + (answer / 0.7)
  db["tokens_used"] = tokens_used
  
  
  return answer