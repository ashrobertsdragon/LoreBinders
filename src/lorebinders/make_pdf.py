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
    from lorebinders._type_annotations import Book, BookDict, Flowable


PAGE_SIZE = LETTER
IMAGE_WIDTH = IMAGE_HEIGHT = 200

STYLE_NORMAL = "Normal"
STYLE_TITLE = "Title"
STYLE_HEADING1 = "Heading1"
STYLE_HEADING2 = "Heading2"
STYLE_HEADING3 = "Heading3"

NamesDict = dict[str, dict[str, list[str] | str] | list[str] | str]


class AfterSection(Enum):
    PAGE_BREAK = PageBreak()
    SPACER = Spacer(1, 12)


def create_detail_list(
    chapters: dict[str, list | str], style: StyleSheet1
) -> list[ListItem]:
    """
    Creates a list of ListItems from a dictionary of chapter summaries.

    Args:
        chapters (dict[str, list | str]): A dictionary of chapter summaries.
        style (StyleSheet1): The style to use for the list items.

    Returns:
        list[ListItem]: A list of ListItems representing the chapter summaries.
    """

    return [
        ListItem(
            Paragraph(
                "\n".join(details)
                if isinstance(details, list)
                else details.replace(", ", "\n"),
                style[STYLE_NORMAL],
            ),
            bulletType="1",
            value=int(chapter),
        )
        for chapter, details in chapters.items()
        if chapter not in ["summary", "image"]
    ]


def setup_toc(style: StyleSheet1) -> TableOfContents:
    """
    Sets up the table of contents.

    Args:
        style (StyleSheet1): The style to use for the table of contents.

    Returns:
        TableOfContents: The table of contents.
    """
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            f"TOCLevel{i}",
            parent=style[STYLE_NORMAL],
            fontSize=12 - 2 * i,
            leading=14 - 2 * i,
            spaceAfter=6 - 3 * i,
            spaceBefore=6 - 3 * i,
            leftIndent=10 * i,
        )
        for i in range(2)
    ]
    return toc


def create_paragraph(text: str, style: StyleSheet1) -> Paragraph:
    """
    Creates a paragraph with the given text and style.

    Args:
        text (str): The text of the paragraph.
        style (StyleSheet1): The style to use for the paragraph.

    Returns:
        Paragraph: The created paragraph.
    """
    return Paragraph(text, style)


def add_item_to_story(
    story: list[Flowable], after_section: AfterSection, *flowables
) -> None:
    """
    Adds one or more flowables to the story.

    Args:
        story (list): The story to add the item to.
        after_section (AfterSection): The item to add after the given items.
        *flowables (Flowable): The Flowable objects to add to the story.
    """
    story.extend(iter(flowables))
    story.append(after_section)


def add_image(story: list[Flowable], image_path: str) -> None:
    """
    Adds an image to the story.

    Args:
        story (list): The story to add the image to.
        image_path (str): The path to the image.
    """
    if os.path.exists(image_path):
        img = Image(image_path, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
        add_item_to_story(story, AfterSection.SPACER, img)


def add_content(
    story: list[Flowable],
    content: NamesDict,
    style: StyleSheet1,
    is_traits: bool = False,
) -> None:
    """
    Adds content to the story.

    Args:
        story (list): The story to add the content to.
        content (dict[str, dict[str, list[str] | str] | list[str] | str]): The
            content to add.
        style (StyleSheet1): The style to use for the content.
        is_traits (bool, optional): Whether the content is for the traits
            section. Defaults to False.
    """
    for key, value in content.items():
        if key in ["summary", "image"]:
            continue
        if is_traits:
            trait = Paragraph(key, style[STYLE_HEADING3])
        detail_list = create_detail_list(
            cast(dict, value) if is_traits else content, style
        )
        details = ListFlowable(detail_list)
        add_item_to_story(
            story,
            AfterSection.PAGE_BREAK,
            *(trait, details) if is_traits else (details,),
        )
        if not is_traits:
            break


def initialize_pdf(metadata: BookDict) -> tuple[SimpleDocTemplate, str]:
    """
    Initializes the PDF document.

    Args:
        metadata (BookDict): The book metadata.

    Returns:
        tuple[SimpleDocTemplate, str]: The initialized PDF document and
        the title.
    """
    title = metadata.title
    author = metadata.author
    folder_name = cast(str, metadata.user_folder)
    output_path = Path(folder_name, f"{title}-lorebinder.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=PAGE_SIZE, author=author, title=title
    )
    return doc, title


def create_pdf(book: Book) -> None:
    """
    Create a PDF file from the chapter summaries.

    Args:
        book (Book): The book object.
    """
    binder: dict[str, dict[str, NamesDict]] = book.binder

    story: list[Flowable] = []
    styles: StyleSheet1 = getSampleStyleSheet()
    doc, title = initialize_pdf(book.metadata)

    title_page = create_paragraph(
        f"LoreBinder\nfor\n{title}", styles[STYLE_TITLE]
    )
    add_item_to_story(story, AfterSection.PAGE_BREAK, title_page)

    toc = setup_toc(styles)
    add_item_to_story(story, AfterSection.PAGE_BREAK, toc)

    def add_toc_entry(flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in [
            STYLE_HEADING1,
            STYLE_HEADING2,
        ]:
            level = 0 if flowable.style.name == STYLE_HEADING1 else 1
            text = flowable.getPlainText()
            toc.addEntry(level, text, doc.page)

    doc.afterFlowable = add_toc_entry

    for category, names in binder.items():
        category_page = create_paragraph(category, styles[STYLE_HEADING1])
        add_item_to_story(story, AfterSection.PAGE_BREAK, category_page)

        for name, content in names.items():
            name_header = create_paragraph(name, styles[STYLE_HEADING2])
            add_item_to_story(story, AfterSection.SPACER, name_header)

            if image_path := cast(str, content.get("image", "")):
                add_image(story, image_path)

            if summary := cast(str, content.get("summary", "")):
                summary_paragraph = create_paragraph(
                    summary, styles[STYLE_NORMAL]
                )
                add_item_to_story(
                    story,
                    AfterSection.SPACER,
                    summary_paragraph,
                )

            add_content(
                story,
                content,
                styles,
                is_traits=(category in ["Characters", "Settings"]),
            )

    doc.multiBuild(story)
