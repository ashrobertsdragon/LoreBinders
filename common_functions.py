import os
import re
import time
import traceback
import openai
import json

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

  messages = [
      {"role": "system", "content": role_char},
      {"role": "user", "content": prompt}
  ]

  if assistant_message:
    messages.append(
      {"role": "assistant"}, {"content": assistant_message},
      {"role": "user", "content": "Please continue from the exact point you left off without any commentary"})
    
  response = openai.ChatCompletion.create(
    model = model,
    messages = messages,
    max_tokens = max_tokens,
    api_key = api_key,
    temperature = temperature
  )

  answer = response.choices[0].message['content'].strip()

  
  return answer