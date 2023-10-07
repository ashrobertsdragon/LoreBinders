import os, re, json, time
from tqdm import tqdm
import common_functions as cf

def initialize_names(chapters, folder_name):
  
  # Determine number of chapters
  num_chapters = len(chapters)
  print(f"\nTotal Chapters: {num_chapters} \n\n")

  # Initialize variables
  chunks_data = []
  character_lists = []

  state_file = os.path.join(folder_name, 'state.json')
  if os.path.exists(state_file):
    print("Reading data from disk...")
    saved_data = cf.read_json_file(state_file)
    chunks_data = saved_data.get("chunks_data", [])
    character_lists = saved_data.get("character_lists", [])


  return chunks_data, character_lists, num_chapters
      
def get_attributes():      # Get attributes

  # Initialize dictionary to store attributs for each chapter
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

def chunk_file(chapters, folder_name):

	chapter_chunks_list = []
	
	for i, chapter in enumerate(chapters):
	# 2000 words appears to be best compromise between performance and accuracy
		words = chapter.split()
		chunks = []
		current_chunk = ""

		for word in words:
			if len(current_chunk) + len(word) <= 2000:
				current_chunk += word + " "
			else:
				chunks.append(current_chunk.strip())
				current_chunk = word + " "

		if current_chunk:
			chunks.append(current_chunk.strip())
		chapter_chunks_list.append((i+1, chunks))


	return chapter_chunks_list

def compare_names(inner_values):

  compared_names = {} 
  
  for i, value_i in enumerate(inner_values):
    for j, value_j in enumerate(inner_values):
      if i != j and value_i != value_j and not value_i.endswith(")") and (value_i.startswith(value_j) or value_i.endswith(value_j)):
          shorter_value, longer_value = sorted([value_i, value_j], key = len)
          compared_names[shorter_value] = longer_value
          
  longer_name = [compared_names.get(name, name) for name in inner_values] 
  inner_values = list(dict.fromkeys(longer_name)) #Deduplicate

  stop_words = ["none", "mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main"] # Entries with these words should be removed
  inner_values = [value for value in inner_values if not any(word in value.lower() for word in stop_words)]


  return inner_values

def sort_names(character_lists):

  parse_tuples = {}
  attribute_table = {}


  for chapter_index, proto_dict in character_lists:


    if chapter_index not in parse_tuples:
      parse_tuples[chapter_index] = proto_dict
    else:
      parse_tuples[chapter_index] += "\n" + proto_dict

  
  for chapter_index, proto_dict in parse_tuples.items():
    
    attribute_table[chapter_index] = {}
    inner_dict = {}
    attribute_name = None
    inner_values = []
      

    lines = proto_dict.split("\n")


    for line in lines:
      
      # Remove lines that need to be removed
      line = re.sub("^[\d.-]\s*", "", line) 
      line = re.sub("^\.\s", "", line)
      if line == "":
        continue
      # Unnecessary attribute_name GPT-3.5 likes to add
      elif "additional" in line.lower():
        continue
      

      character_pattern = re.compile(r"^(.+?)\((major character|minor character|minor characters)\)$", re.IGNORECASE)
      match = re.match(character_pattern, line) 
      
      if match:  
        line = match.group(1) # Drop character roles
      line = line.strip()
      
      #  Remaining lines ending with a colon are attribute names and lines following belong in a list for that attribute
      if line.endswith(":"):
        if attribute_name: 
          inner_dict.setdefault(attribute_name, []).extend(inner_values)
          inner_values = []
        attribute_name = line[:-1].title() 
      else:
        inner_values.append(line)

    if attribute_name: 
      inner_dict.setdefault(attribute_name, []).extend(inner_values)
      inner_values = []
  
    if inner_dict: 
      for attribute_name, inner_values in list(inner_dict.items()):
        inner_values = compare_names(inner_values)
        attribute_table[chapter_index][attribute_name] = inner_values
      inner_values = []

  # Remove empty attribute_name keys 
  for chapter_index in list(attribute_table.keys()):
    for attribute_name, inner_values in list(attribute_table[chapter_index].items()):
      if not inner_values:
        del attribute_table[chapter_index][attribute_name]

  
  return attribute_table

def search_names(chapters, folder_name, chunks_data, character_lists, role_attributes, custom_attributes, chapter_chunks_list, num_chapters):
  
  firstapi_start = time.time()

  # Load state variables
  state = cf.read_state(folder_name)
  i = state.get('i', 0)
  j = state.get('j', 0)

  
  model = "gpt-3.5-turbo"
  max_tokens = 100
  temperature = 0.2
  role_char = f"""You are a script supervisor compiling a list of characters in each scene. For the following selection, determine who are the characters, including major and minor. Please also determine the settings, both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, Kastea, Hell's Kitchen).{custom_attributes}.
If the scene is written in the first person, identify the narrator by their name. Ignore slash characters.
Be as brief as possible, using one or two words for each entry, and avoid descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris field of leftover asteroid pieces' should be 'Asteroid debris field'. ' Unmarked section of wall (potentially a hidden door)' should be 'unmarked wall section'
Exclude any characters, settings, or attributes that are named but not present. For example, if Bob and Sally are talking about Frank or Jamaica, but Frank is not present or they are not in Jamaica, do not list Frank or Jamaica. If you cannot find any mention of a specific attribute in the text, please respond with 'None found' If you are unsure of a setting or no setting is shown in the text, please respond with 'None found'.
Please format the output like this:
Characters:
character1 (major character)
character2 (major character)
character3 (minor character)
Setting:
Setting1 (interior)
Setting2 (exterior)
{role_attributes}"""
  

  with tqdm(total=num_chapters, desc = "\033[92mFinding names\033[0m", unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|", position = 0, leave = True) as pbar_book:
    
    for chapter_index, chunks_tuple in enumerate(chapter_chunks_list):
      chapter_number = chapter_index + 1
      chunks = chunks_tuple[1]
      
      # Create the inner progress bar for chunks
      with tqdm(total=len(chunks), desc = f"\033[92mProcessing Chapter {chapter_number}\033[0m", unit = "Chunk", position = 1, leave = False, bar_format = "|{l_bar}{bar}|", ncols = 40) as pbar_chunk:
        for chunk_index, chunk in enumerate(chunks):
          retry_count = 0
          
          try:
            prompt = f"Text: {chunk}"
            character_list = cf.call_gpt_api(model, prompt, role_char, temperature, max_tokens)
            character_lists.append((chapter_index, character_list))
            
            pbar_chunk.update(1)
            pbar_book.refresh()

          except Exception as e:
            cf.error_handle(e, retry_count, state, i=i, j=j, character_lists=character_lists, chunks=chunks)     # Update the outer progress bar after completing the chapter
            
      pbar_book.update(1)
      

  cf.write_json_file(chunks, f"{folder_name}/chapter_chunks.json")
  cf.write_json_file(character_lists, f"{folder_name}/chapter_lists.json")

  # After the for j loop
  cf.remove_state_file(folder_name)
  firstapi_end = time.time()
  firstapi_total = firstapi_end - firstapi_start
  print(f"First API run: {firstapi_total} seconds")


  return character_lists

def role_description(attribute_table, chapter_index):
  
  # Generate JSON example for characters
  characters = attribute_table[chapter_index].get("Characters", [])
  character_names_JSONex_list = []

  character_names_JSONex_list = [
    f'{character_name}: {{\n'
    'Appearance: {{\n'
    'Eye color: "description",\n'
    'Hair color/style: "description",\n'
    'Height: "description",\n'
    'Weight/build: "description",\n'
    'Clothing and other personal items: "description",\n'
    'Other physical description not otherwise noted: "description"\n'
    '}},\n'
    'Personality: "description",\n'
    'Mood: "description",\n'
    'Relationships: "description",\n'
    'Sexuality: "description",\n'
    '}},\n'
    for character_name in characters
  ]
  # Remove trailing comma  
  character_names_JSONex_list[-1] = character_names_JSONex_list[-1].rstrip(",\n") + "\n"

  character_names_str = ', '.join([f'{character}' for character in characters])
  character_names_JSONex_str = ''.join(character_names_JSONex_list)

  #Generate JSON example for settings
  settings = attribute_table[chapter_index].get("Setting", [])
  if settings:
    setting_names_list = [f'{setting}' for setting in settings]
    setting_names_JSONex_list = [
      '{setting_name}: "description"' for setting_name in settings
    ]

    setting_names_str = ', '.join(setting_names_list)
    setting_names_JSONex_str = ',\n'.join(setting_names_JSONex_list)

    setting_JSONex_str = f'     Setting: {{\n{setting_names_JSONex_str}\n    }}'

  else:
    setting_names_str = ""
    setting_names_JSONex_str = ""
    setting_JSONex_str = ""

  #Generate JSON example for user-defined attributes
  attribute_keys = list(attribute_table[chapter_index].keys())[2:]
  if attribute_keys:
    attribute_data_list = []
    attribute_data_JSONex_list = []
    attributes_JSONex_list = []

    for attribute_key in attribute_keys:
      attribute_values = attribute_table[chapter_index].get(attribute_key,[])

      attribute_values_str = ', '.join(attribute_values)
      attribute_data_list.append(f'{attribute_key}: {attribute_values_str}')
    
      attribute_data_JSONex_list = [
                '{value}: "description"' for value in attribute_values
            ]
      attribute_data_JSONex_str = ',\n'.join(attribute_data_JSONex_list)

      attributes_JSONex_list.append(f'  {attribute_key}: {{\n{attribute_data_JSONex_str}\n  }}')  

    attribute_data_str = ', '.join(attribute_data_list)
    JSON_comma_after_settings = ',\n'
    attributes_JSONex_str = ',\n'.join(attributes_JSONex_list)
    other_attributes_str = f'Also, for the following: {attribute_data_str} . Note any information such as descriptions, any characters or places that might match, etc. Be detailed but concise.'  

  else:
    other_attributes_str = ''
    JSON_comma_after_settings = ''
    attributes_JSONex_str = ''

  # Prepare system role message for GPT-3.5
  role_script = (
    f'You are a developmental editor helping create a story bible. For each character: {character_names_str} in the chapter, note their appearance, personality, mood, relationships with other characters, known or apparent sexuality. Be detailed but concise.\n'  
    f'For each location: {setting_names_str} in the chapter, note how the location is described, where it is in relation to other locations and whether the characters appear to be familiar or unfamilar with the location. Be detailed but concise.\n' 
    'Exclude any characters, trait, name, setting, or attributes that are named but not present. For example, if Bob and Sally are talking about Frank or Jamaica, but Frank is not present or they are not in Jamaica, do not list Frank or Jamaica. If you cannot find any mention of a specific attribute in the text, please respond with "None found" If you are unsure of a setting or no setting is shown in the text, please respond with "None found".\n'  
    f'{other_attributes_str}\n'
    'Please format the output in JSON format. Adhere to proper JSON formatting rules, including escaping special characters like newlines and double quotes. Use the following schema:\n'
    '{\n'
    f'Chapter: "{chapter_index}"\n'
    f'Characters: {{\n{character_names_JSONex_str}\n    }},\n'
    f'{setting_JSONex_str}{JSON_comma_after_settings}'
    f'{attributes_JSONex_str}\n'
    '}'
    ''
    'Please validate that your output is correctly formatted as per JSON standards.'
    )


  return role_script

def clean_json(attribute_summary, json_err, retry_count = 3):

  if retry_count == 0:
    print("cleaning failed")
    exit()

  role_char = "You are an expert at cleaning JSON. You will receive a single property of a larger JSON object. Along with the JSONDecodeError. This may not be the actual problem. Please clean the JSON property and return the entire cleaned JSON property without any other commentary"
  model = "gpt-3.5-turbo-16k"
  temperature = 0.3

  lineno = json_err.lineno
  msg = json_err.msg

  prompt = f"{msg} {lineno}:\n{attribute_summary}"

  max_tokens = int(len(prompt) / 0.7 * 1.10)  # Estimate token size of prompt and add 10% buffer

  attribute_summary = cf.call_gpt_api(model, prompt, role_char, temperature, max_tokens)
    
  try:
    json.loads(attribute_summary)
    print("line cleaned")


    return attribute_summary

  except json.JSONDecodeError as json_err:
    print("Malformed JSON detected. Cleaning")

    
    return clean_json(attribute_summary, json_err, retry_count - 1)
      
def analyze_attributes(chapters, attribute_table, folder_name, num_chapters):
  aa_start = time.time()
  chapter_summaries = []
  
  # State variable status check
  state = cf.read_state(folder_name)
  i = state.get('i', 0) 

  temp_summary_file = f"{folder_name}/chapter_summary.txt"
  chapter_summary_file = f"{folder_name}/chapter_summary.json"
  cf.write_to_file("[", temp_summary_file)

  with tqdm(total=num_chapters, desc = "\033[92mProcessing Book\033[0m", unit = "Chapter", ncols = 40, bar_format = "|{l_bar}{bar}|") as pbar_book:
    for i, chapter in enumerate(chapters):
      attribute_summary = ""
      retry_count = 0
    
      try:
        role_char = role_description(attribute_table, chapter_index = i)
        model = "gpt-3.5-turbo-16k"
        max_tokens = 1000
        temperature = 0.4
        prompt = f"Chapter Text: {chapter}\n\nAnalysis:"  
        attribute_summary = cf.call_gpt_api(model, prompt, role_char, temperature, max_tokens)
        while not attribute_summary.endswith("}\n}"):
          assistant_message = attribute_summary
          attribute_summary += cf.call_gpt_api(model, prompt, role_char,  temperature, max_tokens = 500, assistant_message = assistant_message)

      except Exception as e:
        cf.error_handle(e, retry_count, state, i=i)   

      pbar_book.update()
      
      try:
        json.loads(attribute_summary)
      except json.JSONDecodeError as json_err:
        attribute_summary = clean_json(attribute_summary, json_err)
        
      if i == num_chapters - 1:  # Check if it's the last iteration
        cf.write_to_file(attribute_summary, temp_summary_file)
      else:
        cf.write_to_file(attribute_summary + ",", temp_summary_file)

  cf.write_to_file("]", temp_summary_file)
  
  aa_end = time.time()
  aa_total = aa_end - aa_start
  print(f"Second API run: {aa_total}")
  
  read_text = cf.read_text_file(temp_summary_file)
  jsonified = json.loads(read_text)

  cf.write_json_file(jsonified, chapter_summary_file)
  cf.remove_state_file(folder_name)


  return chapter_summaries

def analyze_book(user_folder, file_path):
  
  full_text = cf.read_text_file(file_path)
  chapters = cf.separate_into_chapters(full_text)

  # Create a folder with the book's name
  sub_folder = os.path.basename(file_path).split('.')[0]
  folder_name = f"{user_folder}/{sub_folder}"
  os.makedirs(folder_name, exist_ok=True)

  # Prep work before doing the real work
  chunks_data, character_lists, num_chapters = initialize_names(chapters, folder_name)
  chapter_chunks_list = chunk_file(chapters, folder_name)

  # Semantic search for attributes in book
  role_attributes, custom_attributes = get_attributes()
  character_lists = search_names(chapters, folder_name, chunks_data, character_lists, role_attributes, custom_attributes, chapter_chunks_list, num_chapters)
  attribute_table = sort_names(character_lists)
  
  cf.write_json_file(attribute_table, f"{folder_name}/attribute_table.json")
  # Semantic search based on attributes pulled
  chapter_summaries = analyze_attributes(chapters, attribute_table, folder_name, num_chapters)
  
  
  return chapter_summaries

