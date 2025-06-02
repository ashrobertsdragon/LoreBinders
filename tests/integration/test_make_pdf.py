import os
from pathlib import Path
from unittest.mock import Mock

import pytest
import tempfile
from PIL import Image as PILImage
from pypdf import PdfReader

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer
)

from lorebinders.make_pdf import AfterSection, create_pdf,create_detail_list, setup_toc, add_item_to_story, initialize_pdf, add_content, add_image

# Fixtures
@pytest.fixture
def get_stylesheet():
    return getSampleStyleSheet()

@pytest.fixture
def temp_output_path():
    with tempfile.TemporaryDirectory() as temp_dirname:
        yield temp_dirname

@pytest.fixture
def binder():
    return {
        "Characters": {
            "Character1": {
                "image": "path/to/image1.jpg",
                "summary": "Summary for Character1",
                "Trait1": {
                    "chapter1": ["detail1", "detail2"],
                    "chapter2": ["detail3"]
                }
            }
        },
        "Settings": {
            "Setting1": {
                "image": "path/to/image2.jpg",
                "summary": "Summary for Setting1",
                "Trait2": {
                    "chapter3": "detail4"
                }
            }
        },
        "Other category": {
            "Item1": {},
            "Item2": {}
        }
    }


def get_pdf_text(file_path):
    reader = PdfReader(file_path)
    return "".join(page.extract_text() for page in reader.pages)

# Tests
# testAfterSection
def test_after_section_page_break_instance():
    from reportlab.platypus import PageBreak
    assert isinstance(AfterSection.PAGE_BREAK.value, PageBreak)

def test_after_section_spacer_instance():
    from reportlab.platypus import Spacer
    spacer = AfterSection.SPACER.value
    assert isinstance(spacer, Spacer)


# test create_detail_list
def test_create_detail_list_generates_list_items():
    chapters = {"1": "Value1", "2": ["Value2", "Value3"], "3": "Value4, Value5"}
    style = getSampleStyleSheet()

    result = create_detail_list(chapters, style)

    assert len(result) == 3
    assert isinstance(ListItem, result[0])
    assert isinstance(ListItem, result[1])
    assert isinstance(ListItem, result[2])

def test_create_detail_list_skips_summary():
    chapters = {
        "1": "Content 1",
        "summary": "Summary Content"
    }
    style = getSampleStyleSheet()
    result = create_detail_list(chapters, style)
    assert len(result) == 1

# test setup_toc
def test_setup_toc_applies_toc_level0_style():
    styles = getSampleStyleSheet()
    toc = setup_toc(styles)
    toc_level0 = toc.levelStyles[0]
    assert toc_level0.fontSize == 12
    assert toc_level0.leading == 14
    assert toc_level0.spaceAfter == 6
    assert toc_level0.spaceBefore == 6

def test_setup_toc_applies_toc_level1_style():
    styles = getSampleStyleSheet()
    toc = setup_toc(styles)
    toc_level1 = toc.levelStyles[1]
    assert toc_level1.fontSize == 10
    assert toc_level1.leading == 12
    assert toc_level1.spaceAfter == 3
    assert toc_level1.spaceBefore == 3
    assert toc_level1.leftIndent == 10

def test_setup_toc_handles_incomplete_styles():
    styles = None
    with pytest.raises(AttributeError):
        setup_toc(styles)

# test add_item_to_story
def test_add_item_to_story_adds_multiple_flowables(get_stylesheet):
    story = []
    flowable1 = Paragraph("Flowable 1", get_stylesheet)
    flowable2 = ListItem(Paragraph("Flowable 3", get_stylesheet), Paragraph("Flowable 4", get_stylesheet))
    add_item_to_story(story, AfterSection.SPACER, flowable1, flowable2)
    assert story == [AfterSection.SPACER, flowable1, flowable2]

def test_add_item_to_story_adds_list_item(get_stylesheet):
    story = []
    flowable = ListItem(Paragraph("Flowable 1", get_stylesheet), Paragraph("Flowable 2", get_stylesheet))
    add_item_to_story(story, AfterSection.PAGE_BREAK, flowable)
    assert story == [AfterSection.PAGE_BREAK, flowable]

def test_add_item_to_story_adds_paragraph(get_stylesheet):
    story = []
    flowable = Paragraph("Flowable", get_stylesheet)
    add_item_to_story(story, flowable, AfterSection.PAGE_BREAK)
    assert story == [AfterSection.PAGE_BREAK, flowable]

def test_add_item_to_story_adds_spacer(get_stylesheet):
    story = []
    flowable = Paragraph("Flowable", get_stylesheet)
    add_item_to_story(story, flowable, AfterSection.SPACER)
    assert story == [AfterSection.SPACER, flowable]

def test_add_item_to_story_appends_after_section(get_stylesheet):
    story = []
    flowable = Paragraph("Flowable", get_stylesheet)
    add_item_to_story(story, AfterSection.PAGE_BREAK, flowable)
    assert story[-1] == AfterSection.PAGE_BREAK

def test_add_item_to_story_handles_empty_flowables(get_stylesheet):
    story = []
    add_item_to_story(story, AfterSection.SPACER)
    assert story == [AfterSection.SPACER]

def test_add_item_to_story_handles_existing_story_list(get_stylesheet):
    flowable = Paragraph("Flowable", get_stylesheet)
    story = [flowable]
    add_item_to_story(story, AfterSection.SPACER, flowable)
    assert story == [flowable, flowable, AfterSection.SPACER]

# add_image tests:
def test_add_image_calls_add_item_to_story_with_image():
    story = []

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_image:
        # Create a small test image
        image = PILImage.new('RGB', (2, 2), color = 'red')
        image.save(temp_image.name)
        temp_image_path = temp_image.name

    result = add_image(story, temp_image_path)
    assert len(result) == 1
    assert isinstance(result[0], Image)
    assert result[0].filename == temp_image_path
    import os
    os.unlink(temp_image_path)

def test_add_image_does_not_add_image_if_path_does_not_exist():
    image_path = "invalid"
    story = []
    result = add_image(story, image_path)
    assert result == story

# test add_content
def test_add_content_adds_trait(get_stylesheet):
    story = []
    style = get_stylesheet()
    content = {"trait": {"1": "Test Trait"}}
    result = add_content(story, content, style, is_traits=True)

    assert len(result) == 2
    assert isinstance(result[0], Paragraph)
    assert isinstance(result[1], ListFlowable)
    assert "trait" in result[0].getPlainText()
    assert len(result[1]._content) == 1
    assert "Test Trait" in result[1]._content[0].getPlainText()

def test_add_content_adds_content_multiple_chapters_is_traits_true(get_stylesheet):
    story = []
    style = get_stylesheet
    content = {"trait": {"1": "Test Content", "2": "Test2", "3": "Test3"}}

    result = add_content(story, content, style, is_traits=True)

    assert len(result) == 2
    assert isinstance(result[0], Paragraph)
    assert isinstance(result[1], ListFlowable)
    assert "trait" in result[0].getPlainText()
    assert len(result[1]._content) == 3
    assert result[1]._content[0].getPlainText() == "Test Content"
    assert result[1]._content[1].getPlainText() == "Test2"
    assert result[1]._content[2].getPlainText() == "Test3"

def test_add_content_adds_content_multiple_chapters_multiple_traits_is_traits_true():
    story = []
    style = get_stylesheet()
    content = {"trait": {"1": "Test Content", "2": "Test2", "3": "Test3"}, "trait2": {"1": "Test4", "2": "Test5", "3": "Test6"}}

    result = add_content(story, content, style, is_traits=True)

    assert len(result) == 4
    assert all(isinstance(item, (Paragraph, ListFlowable)) for item in result)
    assert "trait" in result[0].getPlainText()
    assert "trait2" in result[2].getPlainText()
    assert len(result[1]._content) == 3
    assert len(result[3]._content) == 3
    assert result[1]._content[0].getPlainText() == "Test Content"
    assert result[1]._content[1].getPlainText() == "Test2"
    assert result[1]._content[2].getPlainText() == "Test3"
    assert result[3]._content[0].getPlainText() == "Test4"
    assert result[3]._content[1].getPlainText() == "Test5"
    assert result[3]._content[2].getPlainText() == "Test6"

def test_add_content_adds_content_is_traits_false(get_stylesheet):
    story = []
    style = get_stylesheet
    content = {"1": "Test Content"}

    result = add_content(story, content, style, is_traits=False)

    assert len(result) == 1
    assert isinstance(result[0], ListFlowable)
    assert len(result[0]._content) == 1
    assert "Test Content" in result[0]._content[0].getPlainText()

def test_add_content_adds_content_multiple_chapters_is_traits_false(get_stylesheet):
    story = []
    style = get_stylesheet
    content = {"1": "Test Content", "2": "Test2", "3": "Test3"}

    result = add_content(story, content, style, is_traits=False)

    assert len(result) == 1
    assert isinstance(result[0], ListFlowable)
    assert len(result[0]._content) == 1
    assert result[0]._content[0].getPlainText() == "Test Content"
    assert result[0]._content[1].getPlainText()  == "Test2"
    assert result[0]._content[2].getPlainText()  == "Test3"

def test_add_content_empty_content(get_stylesheet):
    story = []
    style = get_stylesheet()
    content = {}
    result = add_content(story, content, style, is_traits=True)

    assert result == story
    assert len(result) == 0

# test initialize_pdf
def test_initialize_pdf_with_metadata():
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = "Title"
    metadata.author = "Author"
    metadata.user_folder = "test folder"

    doc, title = initialize_pdf(metadata)
    assert title == "Title"
    assert doc.filename == str(Path("test folder", "Title-lorebinder.pdf"))

# test create_pdf

def test_create_pdf(temp_output_path, binder):
    title = "Test Title"
    author = "Test Author"
    user_folder = temp_output_path
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "Test Title" in pdf_text
    assert "Test Author" in pdf_text
    assert "Characters" in pdf_text
    assert "Settings" in pdf_text
    assert "Other category" in pdf_text
    assert "Character1" in pdf_text
    assert "Setting1" in pdf_text
    assert "Item1" in pdf_text
    assert "Item2" in pdf_text

def test_create_pdf_adds_title_page_and_toc(temp_output_path, binder):
    title = "Test Title"
    author = "Test Author"
    user_folder = temp_output_path
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "Table of Contents" in pdf_text
    assert "Test Title" in pdf_text
    assert "LoreBinder" in pdf_text

def test_create_pdf_handles_empty_binder():
    binder = {}
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)

    assert os.path.exists(expected_file_path)
    assert os.path.getsize(expected_file_path) > 0

def test_create_pdf_handles_missing_summary_or_content_fields():
    binder = {"Characters": {"John Doe": {}}}
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "Test Title" in pdf_text
    assert "Test Author" in pdf_text
    assert "Table of Contents" in pdf_text
    assert "Characters" in pdf_text
    assert "John Doe" in pdf_text

def test_create_pdf_properly_adds_summary_paragraphs():
    binder = {
        "Characters": {
            "Protagonist": {
                "image": "protagonist.jpg",
                "summary": "The main character of the story."
            },
            "Antagonist": {
                "summary": "The character who opposes the protagonist."
            }
        },
        "Settings": {
            "Forest": {
                "summary": "A dense forest where the story begins."
            }
        }
    }
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "The main character of the story." in pdf_text
    assert "The character who opposes the protagonist." in pdf_text
    assert "A dense forest where the story begins." in pdf_text

def test_create_pdf_correctly_includes_images():
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_image:
        # Create a small test image
        image = PILImage.new('RGB', (2, 2), color = 'red')
        image.save(temp_image.name)
        temp_image_path = temp_image.name
    binder = {
        "Characters": {
            "John Doe": {"image": "temp_image_path", "summary": "A brave hero"}
        }
    }
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder

    create_pdf(book)
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")
    reader = PdfReader(expected_file_path)
    page = reader.pages[3]

    assert os.path.exists(expected_file_path)
    assert "/XObject" in page["/Resources"]
    assert any("/Filter" in xobj for xobj in page["/Resources"]["/XObject"].values())
    os.unlink(temp_image_path)

def test_create_pdf_adds_category_pages_and_name_headers():
    binder = {
        "Characters": {
            "John Doe": {"summary": "A brave hero", "Test trait": {"1": "Test 1", "2": "Test 2"}}
        },
        "Settings": {
            "Forest": {"summary": "A dense forest", "Test trait": {"1": "Test 1", "2": "Test 2"}}
        }
    }
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "Characters" in pdf_text
    assert "Settings" in pdf_text
    assert "John Doe" in pdf_text
    assert "Forest" in pdf_text
    assert "A brave hero" in pdf_text
    assert "A dense forest" in pdf_text
    assert "Test trait" in pdf_text
    assert "Test 1" in pdf_text
    assert "Test 2" in pdf_text

def test_create_pdf_handles_non_standard_categories():
    binder = {
        "Category1": {
            "Name1": {"summary": "Summary1", "1": "details1"},
            "Name2": {"summary": "Summary2", "2": "details2"}
        },
        "Category2": {
            "Name3": {"summary": "Summary3", "3": "details3"}
        }
    }
    title = "Test Title"
    author = "Test Author"
    user_folder = "user_folder"
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)

    assert os.path.exists(expected_file_path)
    assert "Category1" in pdf_text
    assert "Category2" in pdf_text
    assert "Name1" in pdf_text
    assert "Name2" in pdf_text
    assert "Name3" in pdf_text
    assert "Summary1" in pdf_text
    assert "Summary2" in pdf_text
    assert "Summary3" in pdf_text
    assert "details1" in pdf_text
    assert "details2" in pdf_text
    assert "details3" in pdf_text

def test_verify_table_of_contents_entries_added(temp_output_path, binder):
    title = "Test Title"
    author = "Test Author"
    user_folder = temp_output_path
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    reader = PdfReader(expected_file_path)
    toc_page_text = reader.pages[1].extract_text()

    assert os.path.exists(expected_file_path)
    assert "Table of Contents" in toc_page_text
    assert "Characters" in toc_page_text
    assert "Character1" in toc_page_text
    assert "Settings" in toc_page_text
    assert "Setting1" in toc_page_text
    assert "Other category" in toc_page_text
    assert "Item1" in toc_page_text
    assert "Item2" in toc_page_text
    assert all(str(i) in toc_page_text for i in range(3,9))

def test_create_pdf_document_saved_to_correct_output_path(temp_output_path, binder):
    title = "Test Title"
    author = "Test Author"
    user_folder = temp_output_path
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    assert os.path.exists(expected_file_path)
    assert os.path.getsize(expected_file_path) > 0

def test_validate_order_of_elements_in_pdf_document(temp_output_path,binder):
    title = "Test Title"
    author = "Test Author"
    user_folder = temp_output_path
    book = Mock()
    book.metadata = Mock()
    book.metadata.title = title
    book.metadata.author = author
    book.metadata.user_folder = user_folder
    book.binder = binder
    expected_file_path = os.path.join(temp_output_path, "Test Title-lorebinder.pdf")

    create_pdf(book)
    pdf_text = get_pdf_text(expected_file_path)
    title_index = pdf_text.index("Test Title")
    toc_index = pdf_text.index("Table of Contents")
    characters_index = pdf_text.index("Characters")
    settings_index = pdf_text.index("Settings")
    other_category_index = pdf_text.index("Other category")

    assert os.path.exists(expected_file_path)
    assert title_index < toc_index < characters_index < settings_index < other_category_index
