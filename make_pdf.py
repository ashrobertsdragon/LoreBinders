import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, PageBreak, SimpleDocTemplate, Spacer

from common_functions import read_json_file


def create_pdf(folder_name: str, book_name: str) -> None:
  """
  Create a PDF file from the chapter summaries.
  
  Arguments:
    folder_name: Name of the folder containing the chapter summaries.
    book_name: Name of the book.
  """

  story = []
  toc = []

  input_path = f"{folder_name}/chapter_summaries.json"
  output_path = f"{folder_name}/{book_name}.pdf"
  
  chapter_summaries = read_json_file(input_path)
  
  doc = SimpleDocTemplate(output_path, pagesize =  letter)
  styles = getSampleStyleSheet()

  story.append(Paragraph(book_name, styles["Title"]))

  for attribute, names in chapter_summaries.items():
    toc.append(attribute, doc.page)
    story.append(PageBreak())
    story.append(Paragraph(attribute, styles["Heading1"]))
    story.append(Spacer(1, 12))
    doc.bookmarkPage(attribute)
    
    for name, content in names.items():
      bookmark_name = f"{attribute}_{name}"
      toc.append(name, doc.page)
      story.append(PageBreak())
      story.append(Paragraph(name, styles["Heading2"]))
      story.append(Spacer(1, 12))
      doc.bookmarkPage(bookmark_name)
      
      image_path = content.get("image")
      if image_path and os.path.exists(image_path):
        img = Image(image_path, width = 200, height = 200)
        story.append(img)
        story.append(Spacer(1, 12))

      summary = content.get("summary", "")
      story.append(Paragraph(summary, styles["Normal"]))

      if attribute == "Characters" or attribute == "Settings":
        for trait, chapters in content.items():
          if trait == "summary":
            continue
            
          story.append(Paragraph(trait, styles["Heading3"]))

          detail_list = [ListItem(Paragraph(detail, styles["Normal"]), bulletType = "1", value = int(chapter)) for chapter, detail in chapters.items()]
          story.append(ListFlowable(detail_list))

      else:
        detail_list = [ListItem(Paragraph(detail, styles["Normal"]), bulletType = "1", value = int(chapter)) for chapter, detail in chapters.items()]
        story.append(ListFlowable(detail_list))

  story.insert(2, Paragraph("Table of Contents", styles["Heading1"]))
  for title, page_num in toc:
    story.insert(3, Spacer(1, 12))

  doc.build(story)
