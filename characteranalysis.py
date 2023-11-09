import os, re, time
from tqdm import tqdm
import common_functions as cf

token_conversion_factor = 0.7

def initialize_names(chapters, folder_name):

  num_chapters = len(chapters)
  print(f"\nTotal Chapters: {num_chapters} \n\n")

  character_lists = []

  state_file = os.path.join(folder_name, 'state.json')
  if os.path.exists(state_file):
    print("Reading data from disk...")


  return chunks_data, character_lists, num_chapters
      
def get_attributes():
  dictionary_attributes_list = [] 
  attribute_strings = []

  ask_attributes = input("Besides characters and setting, what other attributes would you like ProsePal to search for (e.g. fantasy races, factions, religions, etc)? Please be as specific as possible. Attributes must be separated by commas for the program to work. Type N if you only want to search for characters and settings\n> ")
  
  if ask_attributes.strip().lower() == "n":
    custom_attributes = ""
    role_attributes = ""
    
  elif ask_attributes.strip() == "":
    custom_attributes = ""
    role_attributes = ""
    
  else:
    custom_attributes = f" and the following additional attributes: {ask_attributes}"
  dictionary_attributes_list = ask_attributes.split(",")

  for attribute in dictionary_attributes_list:
    
    attribute = attribute.strip()
    attribute_string = f"{attribute}:\n{attribute}1\n{attribute}2\n{attribute}3"
    attribute_strings.append(attribute_string)
    role_attributes = "\n".join(attribute_strings)


  return role_attributes, custom_attributes

def ner_role_script():

  role_attributes, custom_attributes = get_attributes()

  role_script = f"""You are a script supervisor compiling a list of characters in each scene. For the following selection, determine who are the characters, giving only their name and no other information. Please also determine the settings, both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, Kastea, Hell's Kitchen).{custom_attributes}.
If the scene is written in the first person, identify the narrator by their name. Ignore slash characters.
Be as brief as possible, using one or two words for each entry, and avoid descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris field of leftover asteroid pieces' should be 'Asteroid debris field'. ' Unmarked section of wall (potentially a hidden door)' should be 'unmarked wall section'
If you cannot find any mention of a specific attribute in the text, please respond with 'None found' on the same line as the attribute name. If you are unsure of a setting or no setting is shown in the text, please respond with 'None found' on the same line as the word 'Setting'
Please format the output exactly like this:
Characters:
character1
character2
character3
Setting:
Setting1 (interior)
Setting2 (exterior)
{role_attributes}"""


  return role_script
def search_names(chapters, folder_name, character_lists, num_chapters):

  role_script = ner_role_script()
  
  firstapi_start = time.time()

  model = "gpt-3.5-turbo-16k"
  max_tokens = 500
  temperature = 0.2

  with tqdm(total=num_chapters, desc="\033[92mFinding names\033[0m", unit="Chapter", ncols=40, bar_format="|{l_bar}{bar}|", position=0, leave=True) as pbar_book:
    for chapter_index, chapter in enumerate(chapters):
      chapter_number = chapter_index + 1

      prompt = f"Text: {chapter}"
      character_list = cf.call_gpt_api(model, prompt, role_script, temperature, max_tokens)
      character_lists.append((chapter_number, character_list))  
      pbar_book.update(1)

  cf.write_json_file(character_lists, f"{folder_name}/chapter_lists.json")
  firstapi_end = time.time()
  firstapi_total = firstapi_end - firstapi_start
  print(f"First API run: {firstapi_total} seconds")


  return character_lists

def role_description(attribute_table, chapter_index):

  characters = attribute_table[chapter_index].get("Characters", [])
  
  characters_list = [
    f'{character_name}:\n'
    'Appearance: description\n'
    'Personality: description\n'
    'Mood: description\n'
    'Relationships: description\n'
    'Sexuality: description\n'
    for character_name in characters
  ]

  characters_str = '\n'.join(characters_list)

  settings = attribute_table[chapter_index].get("Setting", [])
      
  if settings:
    setting_list = [
      f'{setting_name}: description'
      for setting_name in settings
    ]
    
    setting_str = ', '.join(setting_list)
    settings_str = f'Settings:\n{setting_str}\n'

  else:
    setting_str = ''

  attribute_keys = list(attribute_table[chapter_index].keys())[2:]
      
  if attribute_keys:
    attributes_list = []
    for attribute_key in attribute_keys:
      attribute_values = attribute_table[chapter_index].get(attribute_key, [])

      attribute_values_list = [
        f'{value}: description'
        for value in attribute_values
      ]

    attribute_values_str = ', '.join(attribute_values_list)
    attributes_list.append(f'{attribute_key}: {attribute_values_str}\n')
    attribute_str = ''.join(attributes_list)
    attributes_str = f"User Attributes:\n{attribute_str}"

  else:
    attributes_str = ''

  role_script = (
    'You are a developmental editor helping create a story bible. For each character in the chapter, note their appearance, personality, mood, relationships with other characters, known or apparent sexuality. Be detailed but concise.\n'
    'For each location in the chapter, note how the location is described, where it is in relation to other locations and whether the characters appear to be familiar or unfamiliar with the location. Be detailed but concise.\n'
    'If you cannot find any mention of a specific attribute in the text, please respond with "None found". If you are unsure of a setting or no setting is shown in the text, please respond with "None found".\n'
    f'Characters:\n{characters_str}\n'
    f'{settings_str}'
    f'{attributes_str}'
  )


  return role_script
     
def analyze_attributes(chapters, attribute_table, folder_name, num_chapters):

  aa_start = time.time()
  chapter_summaries = []
  chapter_summary_file = f"{folder_name}/chapter_summary.json"

  max_tokens = 1000
  temperature = 0.4

  with tqdm(total=num_chapters, desc = "\033[92mProcessing Book\033[0m", unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as pbar_book:
    for i, chapter in enumerate(chapters):
      attribute_summary = ""
      retry_count = 0
    
      try:
        role_script = role_description(attribute_table, chapter_index = i + 1)
        prompt = f"Chapter Text: {chapter}"  

        #if ((len(role_script) + len(prompt)) / token_conversion_factor) + max_tokens > gpt4_limit:
          #model = "gpt-3.5-turbo-16k"
        #else:
          #model = "gpt-4"
        model = "anthropic/claude-2"
          
        attribute_summary = cf.call_openrouter_api(model, prompt, role_script, temperature, max_tokens)
        while not attribute_summary.endswith("}\n}"):
          assistant_message = attribute_summary
          attribute_summary += cf.call_gpt_api(model, prompt, role_script,  temperature, max_tokens = 500, assistant_message = assistant_message)

      except Exception as e:
        cf.error_handle(e, retry_count)   

      pbar_book.update()
      
    cf.write_text_to_file(attribute_summary, chapter_summary_file)
    chapter_summaries += attribute_summary
    
  aa_end = time.time()
  aa_total = aa_end - aa_start
  print(f"Second API run: {aa_total}")


  return chapter_summaries


def analyze_book(user_folder, file_path):
  
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)

  sub_folder = os.path.basename(file_path).split('.')[0]
  folder_name = f"{user_folder}/{sub_folder}"
  os.makedirs(folder_name, exist_ok=True)

  # Prep work before doing the real work
  character_lists, num_chapters = initialize_names(chapters, folder_name)

  character_lists = search_names(chapters, folder_name, character_lists, num_chapters)
  attribute_table = sort_names(character_lists) 
  cf.write_json_file(attribute_table, f"{folder_name}/attribute_table.json")
  
  # Semantic search based on attributes pulled
  chapter_summaries = analyze_attributes(chapters, attribute_table, folder_name, num_chapters)
  
  
  return chapter_summaries