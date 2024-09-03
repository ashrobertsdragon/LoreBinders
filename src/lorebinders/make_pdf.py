from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, cast

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import (
    ParagraphStyle,
    StyleSheet1,
    getSampleStyleSheet
)
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer
)
from reportlab.platypus.tableofcontents import TableOfContents

if TYPE_CHECKING:
    from lorebinders._type_annotations import Book, BookDict


PAGE_SIZE = LETTER
IMAGE_WIDTH = 200
IMAGE_HEIGHT = 200


class AfterItem(Enum):
    PAGE_BREAK = PageBreak()
    SPACER = Spacer(1, 12)


def create_detail_list(
    chapters: dict[str, list | str], style: ParagraphStyle
) -> list[ListItem]:
    return [
        ListItem(
            Paragraph(
                "\n".join(details) if isinstance(details, list) else details,
                style["Normal"],
            ),
            bulletType="1",
            value=int(chapter),
        )
        for chapter, details in chapters.items()
        if chapter != "summary"
    ]


def setup_toc(styles: StyleSheet1) -> TableOfContents:
    toc = TableOfContents()
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
    toc.levelStyles = [toc_style_attributes, toc_style_names]
    return toc


def create_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def add_item_to_story(story: list, after_item: AfterItem, *items) -> None:
    story.extend(iter(items))
    story.append(after_item)


def initialize_pdf(metadata: BookDict) -> tuple[SimpleDocTemplate, str]:
    title = metadata.title
    author = metadata.author
    if folder_name := metadata.user_folder:
        output_path = Path(folder_name, f"{title}-lorebinder.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=PAGE_SIZE, author=author, title=title
    )
    return doc, title


def create_pdf(book: Book) -> None:
    """
    Create a PDF file from the chapter summaries.

    Arguments:
        folder_name: Name of the folder containing the chapter summaries.
        title: Name of the book.
    """
    binder: dict[str, dict[str, dict[str, dict | str]]] = book.binder

    story: list = []
    styles: StyleSheet1 = getSampleStyleSheet()
    doc, title = initialize_pdf(book.metadata)

    title_page = create_paragraph(f"LoreBinder\nfor\n{title}", styles["Title"])
    add_item_to_story(story, AfterItem.PAGE_BREAK, title_page)

    toc = setup_toc(styles)
    add_item_to_story(story, AfterItem.PAGE_BREAK, toc)

    def add_toc_entry(flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in [
            "Heading1",
            "Heading2",
        ]:
            level = 0 if flowable.style.name == "Heading1" else 1
            text = flowable.getPlainText()
            toc.addEntry(level, text, doc.page)

    doc.afterFlowable = add_toc_entry

    for category, names in binder.items():
        category_page = create_paragraph(category, styles["Heading1"])
        add_item_to_story(story, AfterItem.PAGE_BREAK, category_page)

        for name, content in names.items():
            name_header = create_paragraph(name, styles["Heading2"])
            add_item_to_story(story, AfterItem.SPACER, name_header)

            image_path: str = cast(str, content.get("image", ""))
            if image_path and os.path.exists(image_path):
                img = Image(image_path, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
                add_item_to_story(story, AfterItem.SPACER, img)

            if summary := cast(str, content.get("summary", "")):
                summary_paragraph = create_paragraph(summary, styles["Normal"])
                add_item_to_story(story, AfterItem.SPACER, summary_paragraph)

            if category in {"Characters", "Settings"}:
                for trait, chapters in content.items():
                    if trait == "summary":
                        continue
                    trait_paragraph = create_paragraph(
                        trait, styles["Heading3"]
                    )
                    detail_list = create_detail_list(
                        cast(dict, chapters), styles
                    )
                    add_item_to_story(
                        story,
                        AfterItem.PAGE_BREAK,
                        trait_paragraph,
                        ListFlowable(detail_list),
                    )

            else:
                detail_list = create_detail_list(cast(dict, content), styles)
                add_item_to_story(
                    story,
                    AfterItem.PAGE_BREAK,
                    trait_paragraph,
                    ListFlowable(detail_list),
                )

    doc.multiBuild(story)
