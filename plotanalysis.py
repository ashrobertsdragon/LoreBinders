import openai
import re
import os
import traceback
from common_functions import read_text_file, write_to_file, separate_into_chapters


def role_description():
    role_script = """
    As a developmental editor, your role is to help shape the manuscript at its early stages. Your objective is to analyze the structure, content, and style of the text to make sure it is engaging and clear. In this context, it is important to understand the types of chapters and their significance in progressing the plot. Please pay attention to:
    
    - Pacing and how it affects the flow of the story
    - How the chapter fits into the overall narrative arc
    - Whether the chapter reveals something new about characters or plot
    - If the chapter raises questions or tension that engages the reader
    
    Keep in mind that your goal is to help writers improve their text and to ensure that the narrative is coherent, engaging, and well-structured.
    """
    return role_script

def get_chapter_types():
    chapter_types_file = "chaptertypes.txt"
    with open(chapter_types_file, "r") as file:
        chapter_types = [line.strip() for line in file.readlines() if line.strip()]
    return chapter_types

def story_strucutres():
    story_structures_file = "storystructures.txt"
    with open(story_structures_file, "r") as file:
        story_structure = [line.strip() for line in file.readlines() if line.strip()]
    return story_structure

def get_story_structure_descriptions():
    structure_descriptions_file = "storystructures_description.txt"
    structure_descriptions = {}

    with open(structure_descriptions_file, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line:
            structure_number, structure_description = line.split(".", 1)
            structure_descriptions[structure_number.strip()] = structure_description.strip()

    return structure_descriptions


def analyze_chapter_plot(api_key, chapter_text):
    try:
        prompt = f"{role_description()}\n\nPlease analyze the following chapter text to identify relevant plot points and categorize the type of chapter:{get_chapter_types()}:\n\n{chapter_text}"

        max_tokens = 500
    
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo-16k",
            messages = [{"role": "system", "content": role_description()},
                        {"role": "user", "content": prompt}],
            max_tokens = max_tokens,
            api_key = api_key
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("API Error")
        traceback.print_exc()
        return ""
        exit()

def analyze_story_structure(api_key, chapter_plot_summaries, file_path):
    try:
        text = read_text_file(file_path)
        prompt = f"Pleae compare the chapter summaries to the story beats of story structures: {story_structures()} Identify when a story beat spans multiple chapters.  Name the story structure that the book best follows, and point out where it follows that structure, and where it deviates from it: \n\n{chapter_plot_summaries}"
      
        max_tokens = 500
    
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo-16k",
            messages = [{"role": "system", "content": role_description()},
                        {"role": "user", "content": prompt}],
            max_tokens = max_tokens,
            api_key = api_key
        )
        return response.choices[0].message['content'].strip()
      
        # Get story structure descriptions
        structure_descriptions = get_story_structure_descriptions()

        # Append description to final analysis if a story structure was identified
        for structure_name, structure_description in structure_descriptions.items():
            if structure_name in final_analysis:
                final_analysis += f"\n\nStory Structure Description - {structure_name}: {structure_description}"
                break

        return final_analysis
    except Exception as e:
        print("API Error")
        traceback.print_exc()
        return ""
        exit()

def analyze_book(api_key, text_file_path):
    full_text = read_text_file(text_file_path)
    chapters = separate_into_chapters(full_text)
    chapter_plot_summaries = []

    for i, chapter in enumerate(chapters):
        chapter_plot_summary = analyze_chapter_plot(api_key, chapter)
        print(f"Chapter {i + 1} Plot Summary:\n{chapter_plot_summary}\n")
        chapter_plot_summaries.append(chapter_plot_summary)
        

    # Analyze all of the chapter summaries
    final_analysis = analyze_story_structure(api_key, "\n".join(chapter_plot_summaries), text_file_path)
    print(final_analysis)

    # Create a folder with the book's name
    folder_name = os.path.basename(text_file_path).split('.')[0]
    os.makedirs(folder_name, exist_ok=True)

    # Write summaries and analysis to file
    for i, summary in enumerate(chapter_plot_summaries):
        write_to_file(f"Chapter {i + 1} Plot Summary:\n{summary}\n", f"{folder_name}/chapterplotanalysis.txt")
    write_to_file(final_analysis, f"{folder_name}/finalplotanalysis.txt")

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        exit()
    
    text_file_path = "path_to_your_text_file.txt"  # specify the path to your text file
    
    if not os.path.exists(text_file_path):
        print(f"Error: File '{text_file_path}' not found.")
        exit()

    analyze_book(api_key, text_file_path)