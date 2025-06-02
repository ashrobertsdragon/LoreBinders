from unittest.mock import patch, call, ANY, Mock, MagicMock
import pytest

from lorebinders.make_pdf import AfterSection,create_detail_list, setup_toc, create_paragraph, add_item_to_story,  add_image, add_content, initialize_pdf, create_pdf

# FAKE FIXTURES
# can"t figure out how to create real fixtures for these that work
LETTER = 612.0, 792.0

mock_after_section = Mock()
mock_after_section.PAGE_BREAK = Mock()
mock_after_section.PAGE_BREAK.value = "PAGE_BREAK"
mock_after_section.SPACER = Mock()
mock_after_section.SPACER.value = "SPACER"

# real fixture
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
        }
    }

# TESTS
# after section enum tests
def test_after_section_enum_members_instantiation():
    assert AfterSection.PAGE_BREAK is not None
    assert AfterSection.SPACER is not None

def test_after_section_spacer_instance_dimensions():
    spacer = AfterSection.SPACER.value
    assert spacer.width == 1
    assert spacer.height == 12


# test create_detail_list
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_generates_list_items(mock_list_item, mock_paragraph):
    chapters = {"1": "Value1", "2": ["Value2", "Value3"], "3": "Value4, Value5"}
    style = MagicMock()
    style.name = "Normal"
    
    create_detail_list(chapters, style)
    mock_paragraph.assert_any_call("Value1", style["Normal"])
    mock_paragraph.assert_any_call("Value2\nValue3", style["Normal"])
    mock_paragraph.assert_any_call("Value4\nValue5", style["Normal"])
    assert mock_list_item.call_count == 3

@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_skips_summary(mock_list_item, mock_paragraph):
    chapters = {
        "1": ["Content 1"],
        "summary": "Summary Content"
    }
    style = MagicMock()
    result =create_detail_list(chapters, style)

    mock_paragraph.assert_called_once_with("Content 1", style["Normal"])
    mock_list_item.assert_called_once()
    assert len(result) == 1
    assert result[0] == mock_list_item.return_value

@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_empty_chapters(mock_list_item, mock_paragraph):
    chapters = {}
    style = MagicMock()
    result = create_detail_list(chapters, style)
    assert result == []
    mock_list_item.assert_not_called()
    mock_paragraph.assert_not_called()

@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_non_integer_keys(mock_list_item, mock_paragraph):
    chapters = {"one": ["Content One"]}
    style = MagicMock()
    with pytest.raises(ValueError):
        create_detail_list(chapters, style)  # type: ignore
    mock_list_item.assert_not_called()
    mock_paragraph.assert_called_once()

@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_empty_details_str(mock_list_item, mock_paragraph):
    chapters = {
        "1": ""
    }
    style = MagicMock()
    create_detail_list(chapters, style)  # type: ignore
    mock_paragraph.assert_called_once_with("", style["Normal"])
    mock_list_item.assert_called_once_with(ANY, bulletType="1", value=1)

@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListItem")
def test_create_detail_list_empty_details_list(mock_list_item, mock_paragraph):
    chapters = {
        "1": []
    }
    style = MagicMock()
    create_detail_list(chapters, style)  # type: ignore
    mock_paragraph.assert_called_once_with("", style["Normal"])
    mock_list_item.assert_called_once_with(ANY, bulletType="1", value=1)

# test setup_toc
@patch("lorebinders.make_pdf.TableOfContents")
@patch("lorebinders.make_pdf.ParagraphStyle")
def test_setup_toc_creates_toc_styles(mock_paragraph_style, mock_toc):
    mock_toc_instance = mock_toc.return_value
    style = MagicMock()
    setup_toc(style)
    mock_toc.assert_called_once()
    mock_paragraph_style.assert_has_calls([
        call("TOCLevel0", parent=style["Normal"], fontSize=12, leading=14, spaceAfter=6, spaceBefore=6, leftIndent=0),
        call("TOCLevel1", parent=style["Normal"], fontSize=10, leading=12, spaceAfter=3, spaceBefore=3, leftIndent=10)
    ])
    assert len(mock_toc_instance.levelStyles) == 2
    assert mock_toc_instance.levelStyles[0] == mock_paragraph_style.return_value
    assert mock_toc_instance.levelStyles[1] == mock_paragraph_style.return_value

@patch("lorebinders.make_pdf.TableOfContents")
def test_setup_toc_handles_missing_normal_style(mock_toc):
    style = {}
    with pytest.raises(KeyError):
        setup_toc(style) # type: ignore
    mock_toc.assert_called_once()

# test create_paragraph
@patch("lorebinders.make_pdf.Paragraph")
def test_create_paragraph_valid_text_and_style(mock_paragraph):
    text = "This is a valid paragraph."
    style = MagicMock()

    create_paragraph(text, style)
    mock_paragraph.assert_called_once_with(text, style)

@patch("lorebinders.make_pdf.Paragraph")
def test_create_paragraph_empty_string_and_valid_style(mock_paragraph):
    text = ""
    style = MagicMock()

    create_paragraph(text, style)
    mock_paragraph.assert_called_once_with(text, style)

@patch("lorebinders.make_pdf.Paragraph")
def test_create_paragraph_special_characters_and_valid_style(mock_paragraph):
    text = '!@#$%^&*()_+-=[]{}|;":,.<>/?'
    style = MagicMock()

    create_paragraph(text, style)
    mock_paragraph.assert_called_once_with(text, style)

# test add_item_to_story
@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_adds_multiple_flowables(mock_paragraph):
    story = []
    flowable1 = mock_paragraph("Flowable 1", {"Normal": "test"})
    flowable2 = mock_paragraph("Flowable 2", {"Normal": "test"})
    add_item_to_story(story, mock_after_section.SPACER, flowable1, flowable2)
    assert story == [flowable1, flowable2, mock_after_section.SPACER.value]

@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_appends_after_section(mock_paragraph):
    story = []
    flowable = mock_paragraph("Flowable", {"Normal": "test"})
    add_item_to_story(story, mock_after_section.PAGE_BREAK, flowable)
    assert story[-1] == mock_after_section.PAGE_BREAK.value


@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_handles_empty_story_list(mock_paragraph):
    story = []
    flowable = mock_paragraph("Flowable", {"Normal": "test"})
    add_item_to_story(story, mock_after_section.SPACER, flowable)
    assert story == [flowable, mock_after_section.SPACER.value]


@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_handles_empty_flowables_argument(mock_paragraph):
    story = []
    add_item_to_story(story, mock_after_section.PAGE_BREAK)
    assert story == [mock_after_section.PAGE_BREAK.value]
    mock_paragraph.assert_not_called()

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_handles_none_story_list(mock_paragraph):
    story = None
    with pytest.raises(AttributeError):
        add_item_to_story(story, mock_after_section.SPACER) #type: ignore
    mock_paragraph.assert_not_called()


@patch("lorebinders.make_pdf.Paragraph")
def test_add_item_to_story_handles_existing_story_list(mock_paragraph):
    flowable1 = mock_paragraph("Flowable", {"Normal": "test"})
    story = [flowable1]
    flowable2 = mock_paragraph("Flowable", {"Normal": "test"})
    add_item_to_story(story, mock_after_section.PAGE_BREAK, flowable1)
    assert story == [flowable1, flowable2, mock_after_section.PAGE_BREAK.value]

# test add_image
@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.os.path.exists")
@patch("lorebinders.make_pdf.Image")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_image_calls_add_item_to_story_with_image(mock_add_item_to_story, mock_image, mock_exists):
    mock_exists.return_value = True
    story = []
    image_path = "path/to/image.jpg"
    add_image(story,image_path)
    mock_add_item_to_story.assert_called_once_with(ANY, mock_after_section.SPACER, mock_image.return_value)
    mock_image.assert_called_once_with(image_path, width=200, height=200)

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.os.path.exists")
@patch("lorebinders.make_pdf.Image")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_image_does_not_add_image_if_path_does_not_exist(mock_add_item_to_story, mock_image, mock_exists):
    mock_exists.return_value = False
    image_path = "invalid"
    story = []
    add_image(story,image_path)
    mock_add_item_to_story.assert_not_called()
    mock_image.assert_not_called()

# test add_content
@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_trait(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"trait": {"1": "Test Trait"}}

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_called_once_with("trait", style["Heading3"])
    mock_create_detail_list.assert_called_once()
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once()

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_multiple_traits(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"trait1": {"1": "Test Trait"}, "trait2": {"1": "Test Trait"}, "trait3": {"1": "Test Trait"}}

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_has_calls([call("trait1", style["Heading3"]), call("trait2", style["Heading3"]), call("trait3", style["Heading3"])])
    assert mock_create_detail_list.call_count ==3
    assert mock_list_flowable.call_count == 3
    assert mock_add_item_to_story.call_count == 3

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_content_is_traits_true(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"trait": {"1": "Test Trait"}}

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_called_once()
    mock_create_detail_list.assert_called_once_with({"1": "Test Trait"}, style)
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once_with(story, mock_after_section.PAGE_BREAK, mock_paragraph.return_value, mock_list_flowable.return_value)

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_skips_image_and_summary(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"image": "image_path", "summary": "test summary", "trait": {"1": "Test Trait"}}

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_called_once()
    mock_create_detail_list.assert_called_once_with({"1": "Test Trait"}, style)
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once_with(story, mock_after_section.PAGE_BREAK, mock_paragraph.return_value, mock_list_flowable.return_value)

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_content_multiple_chapters_is_traits_true(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"trait": {"1": "Test Content", "2": "Test2", "3": "Test3"}}

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_called_once()
    mock_create_detail_list.assert_called_once_with({"1": "Test Content", "2": "Test2", "3": "Test3"}, style)
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once_with(story, mock_after_section.PAGE_BREAK, mock_paragraph.return_value, mock_list_flowable.return_value)

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_content_multiple_chapters_multiple_traits_is_traits_true(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"trait": {"1": "Test Content", "2": "Test2", "3": "Test3"}, "trait2": {"1": "Test4", "2": "Test5", "3": "Test6"}}
    mock_story = Mock()
    mock_add_item_to_story.return_value = mock_story

    add_content(story, content, style, is_traits=True)

    mock_paragraph.assert_has_calls([call("trait", style["Heading3"]), call("trait2", style["Heading3"])])
    mock_create_detail_list.assert_has_calls([call({"1": "Test Content", "2": "Test2", "3": "Test3"}, style), call({"1": "Test4", "2": "Test5", "3": "Test6"}, style)])
    assert mock_list_flowable.call_count == 2
    mock_add_item_to_story.assert_has_calls([call(story, mock_after_section.PAGE_BREAK, mock_paragraph.return_value, mock_list_flowable.return_value), call(mock_story, mock_after_section.PAGE_BREAK, mock_paragraph.return_value, mock_list_flowable.return_value)])

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_content_is_traits_false(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"1": "Test Content"}

    add_content(story, content, style, is_traits=False)

    mock_paragraph.assert_not_called()
    mock_create_detail_list.assert_called_once_with(content, style)
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once_with(story, mock_after_section.PAGE_BREAK, mock_list_flowable.return_value)

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.Paragraph")
@patch("lorebinders.make_pdf.ListFlowable")
@patch("lorebinders.make_pdf.create_detail_list")
@patch("lorebinders.make_pdf.add_item_to_story")
def test_add_content_adds_content_multiple_chapters_is_traits_false(mock_add_item_to_story, mock_create_detail_list, mock_list_flowable, mock_paragraph):
    story = []
    style = MagicMock()
    content = {"1": "Test Content", "2": "Test2", "3": "Test3"}

    add_content(story, content, style, is_traits=False)

    mock_paragraph.assert_not_called()
    mock_create_detail_list.assert_called_once_with(content, style)
    mock_list_flowable.assert_called_once_with(mock_create_detail_list.return_value)
    mock_add_item_to_story.assert_called_once_with(story, mock_after_section.PAGE_BREAK, mock_list_flowable.return_value)

# test initialize_pdf
@patch("lorebinders.make_pdf.Path")
@patch("lorebinders.make_pdf.SimpleDocTemplate")
def test_initialize_pdf_with_metadata(mock_simple_doc_template, mock_path):
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = "Test Title"
    metadata.author = "Test Author"
    metadata.user_folder = "test_folder"

    initialize_pdf(metadata)

    mock_path.assert_called_once_with("test_folder", "Test Title-lorebinder.pdf")
    mock_simple_doc_template.assert_called_once_with(
        str(mock_path.return_value),
        pagesize=LETTER,
        author="Test Author",
        title="Test Title"
    )

@patch("lorebinders.make_pdf.Path")
@patch("lorebinders.make_pdf.SimpleDocTemplate")
def test_initialize_pdf_returns_correct_title(mock_simple_doc_template, mock_path):
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = "Correct Title"
    metadata.author = "Test Author"
    metadata.user_folder = "test_folder"
    _, title = initialize_pdf(metadata)
    assert title == "Correct Title"
    mock_path.assert_called_once()
    mock_simple_doc_template.assert_called_once()

@patch("lorebinders.make_pdf.Path")
@patch("lorebinders.make_pdf.SimpleDocTemplate")
def test_initialize_pdf_creates_pdf_in_user_folder(mock_simple_doc_template, mock_path):
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = "Test Title"
    metadata.author = "Test Author"
    metadata.user_folder = "specified_folder"
    initialize_pdf(metadata)
    mock_simple_doc_template.assert_called_once_with(
        str(mock_path.return_value),
        pagesize=LETTER,
        author="Test Author",
        title="Test Title"
    )

@patch("lorebinders.make_pdf.Path")
@patch("lorebinders.make_pdf.SimpleDocTemplate")
def test_initialize_pdf_empty_title(mock_simple_doc_template, mock_path):
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = ""
    metadata.author = "Test Author"
    metadata.user_folder = "test_folder"
    doc, title = initialize_pdf(metadata)
    mock_simple_doc_template.assert_called_once_with(
        str(mock_path.return_value),
        pagesize=LETTER,
        author="Test Author",
        title=""
    )
    assert title == ""
    assert doc is not None

@patch("lorebinders.make_pdf.Path")
@patch("lorebinders.make_pdf.SimpleDocTemplate")
def test_initialize_pdf_empty_author(mock_simple_doc_template, mock_path):
    mock_book_dict = Mock()
    metadata = mock_book_dict.return_value
    metadata.title = "Test Title"
    metadata.author = ""
    metadata.user_folder = "test_folder"
    doc, title = initialize_pdf(metadata)
    mock_simple_doc_template.assert_called_once_with(
        str(mock_path.return_value),
        pagesize=LETTER,
        author="",
        title="Test Title"
    )
    assert title == "Test Title"
    assert doc is not None

# test create_pdf
@patch("lorebinders.make_pdf.cast")
@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.add_image")
@patch("lorebinders.make_pdf.add_content")
@patch("lorebinders.make_pdf.add_item_to_story")
@patch("lorebinders.make_pdf.create_paragraph")
@patch("lorebinders.make_pdf.setup_toc")
@patch("lorebinders.make_pdf.initialize_pdf")
def test_create_pdf_successfully_creates_pdf(mock_initialize_pdf, mock_setup_toc, mock_create_paragraph, mock_add_item_to_story, mock_add_content, mock_add_image, mock_cast):
    binder = {"Characters": {"John Doe": {"summary": "A brave hero"}}}
    book = Mock()
    book.binder = binder
    book.metadata = Mock()
    book.metadata.title = "Test Book"
    book.metadata.author = "Test Author"
    
    mock_doc = Mock()
    mock_multiBuild = Mock()
    mock_doc.multiBuild = mock_multiBuild
    mock_initialize_pdf.return_value = (mock_doc, "Test Book")
    mock_create_paragraph.return_value = Mock()
    mock_cast.side_effect = lambda type_arg, value: str(value) if value else ""
    
    mock_styles = MagicMock()

    create_pdf(book, mock_styles)

    mock_initialize_pdf.assert_called_once_with(book.metadata)
    mock_setup_toc.assert_called_once()
    mock_create_paragraph.assert_any_call("LoreBinder\nfor\nTest Book\nTest Author", mock_styles["Title"])
    mock_add_item_to_story.assert_any_call(ANY, mock_after_section.PAGE_BREAK, ANY)
    mock_add_image.assert_not_called()
    mock_add_content.assert_called_once()
    mock_multiBuild.assert_called_once()

@patch("lorebinders.make_pdf.cast")
@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.add_image")
@patch("lorebinders.make_pdf.add_content")
@patch("lorebinders.make_pdf.add_item_to_story")
@patch("lorebinders.make_pdf.create_paragraph")
@patch("lorebinders.make_pdf.setup_toc")
@patch("lorebinders.make_pdf.initialize_pdf")
def test_create_pdf_adds_title_page_and_toc(mock_initialize_pdf, mock_setup_toc, mock_create_paragraph, mock_add_item_to_story, mock_add_content, mock_add_image, mock_cast, binder):
    
    book = Mock()
    book.binder = binder
    book.metadata = Mock()
    book.metadata.title = "Test Book"
    book.metadata.author = "Test Author"
    
    mock_doc = Mock()
    mock_multiBuild = Mock()
    mock_doc.multiBuild = mock_multiBuild
    mock_initialize_pdf.return_value = (mock_doc, "Test Book")
    mock_create_paragraph.return_value = Mock()
    mock_cast.side_effect = lambda type_arg, value: str(value) if value else ""
    
    mock_styles = MagicMock()

    create_pdf(book, mock_styles)

    mock_create_paragraph.assert_any_call("LoreBinder\nfor\nTest Book\nTest Author", mock_styles["Title"])
    mock_setup_toc.assert_called_once()
    mock_add_item_to_story.assert_any_call(ANY, mock_after_section.PAGE_BREAK, ANY)
    assert mock_add_content.call_count == 2
    assert mock_add_image.call_count == 2

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.add_image")
@patch("lorebinders.make_pdf.add_content")
@patch("lorebinders.make_pdf.add_item_to_story")
@patch("lorebinders.make_pdf.create_paragraph")
@patch("lorebinders.make_pdf.setup_toc")
@patch("lorebinders.make_pdf.initialize_pdf")
def test_create_pdf_handles_empty_binder(mock_initialize_pdf, mock_setup_toc, mock_create_paragraph, mock_add_item_to_story,  mock_add_content, mock_add_image):
    book = Mock()
    book.binder = {}
    book.metadata = Mock()
    book.metadata.title = "Test Book"
    book.metadata.author = "Test Author"
    mock_doc = Mock()
    mock_multiBuild = Mock()
    mock_doc.multiBuild = mock_multiBuild
    mock_initialize_pdf.return_value = (mock_doc, "Test Book")
    mock_create_paragraph.return_value = Mock()
    
    mock_styles = MagicMock()

    create_pdf(book, mock_styles)

    mock_initialize_pdf.assert_called_once_with(book.metadata)
    mock_setup_toc.assert_called_once()
    mock_create_paragraph.assert_any_call("LoreBinder\nfor\nTest Book\nTest Author", mock_styles["Title"])
    mock_add_item_to_story.assert_any_call(ANY, mock_after_section.PAGE_BREAK, ANY)
    mock_add_content.assert_not_called()
    mock_add_image.assert_not_called()
    mock_multiBuild.assert_called_once()

@patch("lorebinders.make_pdf.AfterSection", mock_after_section)
@patch("lorebinders.make_pdf.add_image")
@patch("lorebinders.make_pdf.add_content")
@patch("lorebinders.make_pdf.add_item_to_story")
@patch("lorebinders.make_pdf.create_paragraph")
@patch("lorebinders.make_pdf.setup_toc")
@patch("lorebinders.make_pdf.initialize_pdf")
def test_create_pdf_handles_missing_summary_or_content_fields(mock_initialize_pdf, mock_setup_toc, mock_create_paragraph, mock_add_item_to_story, mock_add_content, mock_add_image):
    binder = {"Characters": {"John Doe": {}}}
    book = Mock()
    book.binder = binder
    book.metadata = Mock()
    book.metadata.title = "Test Book"
    book.metadata.author = "Test Author"
    mock_doc = Mock()
    mock_multiBuild = Mock()
    mock_doc.multiBuild = mock_multiBuild
    mock_initialize_pdf.return_value = (mock_doc, "Test Book")
    mock_create_paragraph.return_value = Mock()
    
    mock_styles = MagicMock()
    
    create_pdf(book, mock_styles)

    mock_initialize_pdf.assert_called_once_with(book.metadata)
    mock_setup_toc.assert_called_once()
    mock_create_paragraph.assert_has_calls([
        call("LoreBinder\nfor\nTest Book\nTest Author", mock_styles["Title"]),
        call("Table of Contents", mock_styles["Heading1"]),
        call("Characters", mock_styles["Heading1"]),
        call("John Doe", mock_styles["Heading2"])
    ])
    assert mock_add_item_to_story.call_count == 5
    mock_add_image.assert_not_called()
    mock_add_content.assert_called_once()
    mock_multiBuild.assert_called_once()

def test_add_toc_entry():
    from reportlab.platypus import Paragraph, ListFlowable
    doc = Mock()
    doc.page = 1
    toc = Mock()
    toc.addEntry = Mock()

    def paragraph_factory(text: str, style_name: str):
        mock_paragraph = Mock(spec=Paragraph)
        mock_paragraph.style = MagicMock()
        mock_paragraph.style.name = style_name
        mock_paragraph.getPlainText.return_value = text
        return mock_paragraph

    title_paragraph = paragraph_factory("LoreBinder\nfor\nTest Title", "Title")
    characters_paragraph = paragraph_factory("Characters", "Heading1")
    name_paragraph = paragraph_factory("John Doe", "Heading2")
    summary_paragraph = paragraph_factory("Summary", "Heading3")
    trait_paragraph = paragraph_factory("Trait", "Heading3")
    list_flowable = Mock(spec=ListFlowable)
    list_flowable.style = MagicMock()
    list_flowable.style.name = "Normal"

    # Copy the add_toc_entry function from the make_pdf module since it cannot be tested directly
    def add_toc_entry(flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in [
            "Heading1",
            "Heading2",
        ]:
            level = 0 if flowable.style.name == "Heading1" else 1
            text = flowable.getPlainText()
            toc.addEntry(level, text, doc.page)


    add_toc_entry(title_paragraph)
    toc.addEntry.assert_not_called()

    add_toc_entry(characters_paragraph)
    toc.addEntry.assert_called_once_with(0, "Characters", doc.page)

    toc.reset_mock()
    add_toc_entry(name_paragraph)
    toc.addEntry.assert_called_once_with(1, "John Doe", doc.page)

    toc.reset_mock()
    add_toc_entry(summary_paragraph)
    toc.addEntry.assert_not_called()

    toc.reset_mock()
    add_toc_entry(trait_paragraph)
    toc.addEntry.assert_not_called()

    toc.reset_mock()
    add_toc_entry(list_flowable)
    toc.addEntry.assert_not_called()