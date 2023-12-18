import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, PageBreak, SimpleDocTemplate, Spacer, TableOfContents

from common_functions import read_json_file


def create_pdf(folder_name: str, book_name: str) -> None:
  """
  Create a PDF file from the chapter summaries.
  
  Arguments:
    folder_name: Name of the folder containing the chapter summaries.
    book_name: Name of the book.
  """

  story = []

  input_path = os.path.join(folder_name, "chapter_summaries.json")
  output_path = os.path.join(folder_name, f"{book_name}.pdf")

  folder_split = folder_name.split('/')
  user_name = folder_split[0]
  
  chapter_summaries = read_json_file(input_path)
  
  doc = SimpleDocTemplate(output_path, pagesize =  letter, author = user_name, title = book_name)
  styles = getSampleStyleSheet()
  toc_style = ParagraphStyle('TOCHeading', parent = styles['Heading2'], spaceAfter = 10)

  story.append(Paragraph(book_name, styles["Title"]), PageBreak())

  toc = TableOfContents()
  toc.levelStyles = [toc_style]
  story.append(toc)
  story.append(PageBreak())

  for attribute, names in chapter_summaries.items():
    story.append(Paragraph(attribute, styles["Heading1"]))
    doc.bookmarkPage(attribute)
    story.append(Spacer(1, 12))
    
    for name, content in names.items():
      bookmark_name = f"{attribute}_{name}"
      story.append(PageBreak())
      story.append(Paragraph(name, styles["Heading2"]))
      doc.bookmarkPage(bookmark_name)
      story.append(Spacer(1, 12))
      
      image_path = content.get("image")
      if image_path and os.path.exists(image_path):
        img = Image(image_path, width = 200, height = 200)
        story.append(img)
        story.append(Spacer(1, 12))

      summary = content.get("summary", "")
      story.append(Paragraph(summary, styles["Normal"]))
      story.append(Spacer(1, 12))

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

  doc.build(story)
