import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

from file_handling import FileHandler

file_handler = FileHandler()


def create_pdf(folder_name: str, title: str) -> None:
    """
    Create a PDF file from the chapter summaries.

    Arguments:
        folder_name: Name of the folder containing the chapter summaries.
        title: Name of the book.
    """

    story = []

    input_path = os.path.join(folder_name, "lorebinder.json")
    output_path = os.path.join(folder_name, f"{title}-lorebinder.pdf")

    folder_split = folder_name.split("/")
    user_name = folder_split[0]

    chapter_summaries = file_handler.read_json_file(input_path)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter, author=user_name, title=title
    )
    styles = getSampleStyleSheet()

    toc_style_attributes = ParagraphStyle(
        "TOCLevel0",
        parent=styles["Normal"],
        fontSize=12,
        leading=14,
        spaceAfter=6,
        spaceBefore=6,
    )

    toc_style_names = ParagraphStyle(
        "TOCLevel1",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        spaceAfter=3,
        spaceBefore=3,
        leftIndent=10,
    )

    story.append(Paragraph(f"LoreBinder\nfor\n{title}", styles["Title"]))
    story.append(PageBreak())

    toc = TableOfContents()
    toc.levelStyles = [toc_style_attributes, toc_style_names]
    story.append(toc)
    story.append(PageBreak())

    def add_toc_entry(flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in [
            "Heading1",
            "Heading2",
        ]:
            level = 0 if flowable.style.name == "Heading1" else 1
            text = flowable.getPlainText()
            toc.addEntry(level, text, doc.page)

    def create_detail_list(chapters: dict) -> list:
        detail_list = []
        for chapter, details in chapters.items():
            if chapter == "summary":
                continue
            detail_string = "\n".join(str(detail) for detail in details)
            list_item = ListItem(
                Paragraph(detail_string, styles["Normal"]),
                bulletType="1",
                value=int(chapter),
            )
            detail_list.append(list_item)
        return detail_list

    doc.afterFlowable = add_toc_entry

    for attribute, names in chapter_summaries.items():
        story.append(Paragraph(attribute, styles["Heading1"]))
        story.append(PageBreak())

        for name, content in names.items():
            story.append(Paragraph(name, styles["Heading2"]))
            story.append(Spacer(1, 12))

            image_path = content.get("image")
            if image_path and os.path.exists(image_path):
                img = Image(image_path, width=200, height=200)
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
                    detail_list = create_detail_list(chapters)
                    story.append(ListFlowable(detail_list))

            else:
                story.append(Paragraph(trait, styles["Heading3"]))
                detail_list = create_detail_list(content)
                story.append(ListFlowable(detail_list))
            story.append(PageBreak())

    doc.multiBuild(story)
