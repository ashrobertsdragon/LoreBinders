import os
import re

import ebooklib
import docx
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

def read_epub(file_path: str) -> str:
  """
  Reads the contents of an epub file and returns it as a string.

  Arguments:
    file_path: Path to the epub file.

  Returns the contents of the epub file as a string.
  """

  return ebooklib.epub.read_epub(file_path)

def read_docx(file_path: str) -> str:
  """
  Reads the contents of a docx file and returns it as a string.
  
  Arguments:
    file_path: Path to the docx file.

  Returns the contents of the docx file as a string.
  """

  doc = docx.Document(file_path)


  return "\n".join([paragraph.text for paragraph in doc.paragraphs])

  
def read_pdf(file_path: str) -> str:
  """
  Reads the contents of a pdf file and returns it as a string.
  
  Arguments:
    file_path: Path to the pdf file.
  
  Returns the contents of the pdf file as a string.
  """

  pdf = PdfFileReader(open(file_path, "rb"))

  return "\n".join([pdf.getPage(i).extractText() for i in range(pdf.numPages)])

def convert_file(book_name: str, folder_name: str) -> str:
  """
  Converts a book to a text file with 3 asterisks for chapter breaks
  
  Arguments:
    book_name: Name of the book.
    folder_name: Name of the folder containing the book.

  Reutrns the name of the text file.
  """

  file_path = f"{folder_name}/{book_name}"

  filename_list = book_name.split(".")
  if len(filename_list) > 1:
    base_name = "_".join(filename_list[:-1])
  extension = filename_list[-1]
  
  if extension == "epub":
    book_content = read_epub(file_path)
  elif extension == "docx":
    book_content = read_docx(file_path)
  elif extension == "pdf":
    book_content = read_pdf(file_path)
  elif extension == "txt" or extension == "text":
    book_content = read_text_file(file_path)
  else:
    print("Invalid filetype")

  book_content = convert_chapter_break(file_path)

  book_name = f"{base_name}.txt"
  write_to_file(book_content, book_name)


  return book_name
  