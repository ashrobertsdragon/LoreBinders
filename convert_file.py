import os
import re
from Typing import Tuple

import ebooklib
import docx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileReader

from common_functions import read_text_file, write_to_file

CHAPTER_PATTERN = re.compile(r"^\s*chapter\s|\schapter\s*$", re.IGNORECASE)

def detect_chapter(line: str) -> bool:
  """
  Detects if a line is a chapter header.
  """
  return CHAPTER_PATTERN.match(line) is not None

def convert_chapter_break(book_content: str) -> str:
  """
  Converts chapter breaks to three askerisks
  
  Arguments:
  book_content: The content of the book.
  
  Returns the book content with askerisks for chapter breaks."""

  book_lines = book_content.split("\n")
  for i, line in enumerate(book_lines):
    if detect_chapter(line):
      book_lines[i] = "***"


  return "\n".join(book_lines)  

def read_epub(file_path: str) -> Tuple[str: dict]:
  """
  Reads the contents of an epub file and returns it as a string.

  Arguments:
    file_path: Path to the epub file.

  Returns the contents of the epub file as a string.
  """

  chapter_files = []
  commbined_content = []
  metadata = {}
  
  book = ebooklib.epub.read_epub(file_path)

  opf_file = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_PACKAGE][0]
  opf_content = opf_file.get_content()

  root = ET.fromstring(opf_content)
  ns = {"opf": "http://www.idpf.org/2007/opf"}
  
  manifest_items = root.findall(".//opf.item", ns)
  guide_items = root.findall(".//opf:reference", ns)
  toc_in_guide = any(reference.get("type", "") == "toc" for reference in guide_items)

  metadata["title"] = book.get_metadata("dc", "title")
  metadata["author"] = book.get_metadata("dc", "creator")

  for item in manifest_items:
    item_id = item.attrib.get("id", "")
    item_href = item.attrib.get("href", "")

    if "text" in item_href.lower() and not toc_in_guide:

      if re.match(r"id[0-9]+", item_id.lower):
        chapter_files.append(item_href)
      elif "section" in item_id.lower():
        chapter_files.append(item_href)
      elif "chapter" in item_id.lower:
        chapter_files.append(item_href)
      elif re.match(r"c[0-9]+", item_id.lower):
        chapter_files.append(item_href)
      elif "content" in item_id.lower and all(x not in item_href for x in ["title", "copyright", "intoduction"]):
        chapter_files.append(item_href)    

    for chapter in chapter_files:
      item = book.get_item_with_href(chapter)
      soup = BeautifulSoup(item.content, "html.parser")
      text = soup.get_text()
      commbined_content.append(text)

    book_content = "\n***\n"
      
  return book_content, metadata

def read_docx(file_path: str) -> str:
  """
  Reads the contents of a docx file and returns it as a string.
  
  Arguments:
    file_path: Path to the docx file.

  Returns the contents of the docx file as a string.
  """
  
  metadata = {}

  doc = docx.Document(file_path)
  
  book_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])

  core_properties = doc.core_properties
  metadata["title"] = core_properties.title
  metadata["author"] = core_properties.author

  return book_content, metadata

  
def read_pdf(file_path: str) -> Tuple[str, str]:
  """
  Reads the contents of a pdf file and returns it as a string.
  
  Arguments:
    file_path: Path to the pdf file.
  
  Returns the contents of the pdf file as a string.
  """

  metadata = {}
  
  pdf = PdfFileReader(open(file_path, "rb"))
  book_content = "\n".join([pdf.getPage(i).extractText() for i in range(pdf.numPages)])

  doc_info = pdf.documentInfo
  metadata["title"] = doc_info.title
  metadata["author"] = doc_info.author

  return book_content, metadata

def convert_file(book_name: str, folder_name: str) -> str:
  """
  Converts a book to a text file with 3 asterisks for chapter breaks
  
  Arguments:
    book_name: Name of the book.
    folder_name: Name of the folder containing the book.

  Reutrns the name of the text file.
  """

  book_content = ""
  file_path = f"{folder_name}/{book_name}"

  filename_list = book_name.split(".")
  if len(filename_list) > 1:
    base_name = "_".join(filename_list[:-1])
  extension = filename_list[-1]
  
  if extension == "epub":
    book_content, metadata = read_epub(file_path)
  elif extension == "docx":
    book_content, metadata = read_docx(file_path)
  elif extension == "pdf":
    book_content, metadata = read_pdf(file_path)
  elif extension == "txt" or extension == "text":
    book_content, metadata = read_text_file(file_path)
  else:
    print("Invalid filetype")
    exit()

  book_content = convert_chapter_break(book_content)

  book_name = f"{base_name}.txt"
  write_to_file(book_content, book_name)


  return book_content, book_name
  