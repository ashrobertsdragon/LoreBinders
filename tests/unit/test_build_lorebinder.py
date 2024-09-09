from unittest.mock import MagicMock, patch, call

import pytest

import lorebinders.start_ai_initialization as start_ai_initialization
from lorebinders.book import Book, Chapter
from lorebinders.book_dict import BookDict
from lorebinders.ai.ai_models.json_file_model_handler import JSONFileProviderHandler
from lorebinders.ai.rate_limiters.file_rate_limit_handler import FileRateLimitHandler
from lorebinders.build_lorebinder import (
    create_book,
    build_binder,
    start,
    summarize_names,
    perform_ner,
    analyze_names,
    summarize
)

@pytest.fixture
def mock_ner():
    return MagicMock()

@pytest.fixture
def mock_analyzer():
    return MagicMock()

@pytest.fixture
def mock_summarizer():
    return MagicMock()

@pytest.fixture
def mock_metadata():
    return BookDict(author="Test Author", title="Test Book", book_file="test.txt")

@pytest.fixture
def mock_chapter():
    return MagicMock(spec=Chapter)

@pytest.fixture
def mock_book():
    return MagicMock(spec=Book)

def test_create_book_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"

    with pytest.raises(Exception):
        create_book(book_dict)

@patch("lorebinders.book.read_text_file")
def test_create_book(mock_read_text_file):
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.txt"

    mock_read_text_file.return_value = "Mocked book content"

    result = create_book(book_dict)

    assert isinstance(result, Book)
    mock_read_text_file.assert_called_once_with(book_dict.book_file)

@patch("lorebinders.build_lorebinder.name_extractor")
def test_perform_ner(mock_name_extractor):
    mock_ai = "mock ai"
    mock_metadata = MagicMock()
    mock_metadata.narrator = "test narrator"
    mock_metadata.custom_categories = []
    expected_result = {"expected": "result"}
    mock_chapter = MagicMock()
    mock_name_extractor.build_role_script.return_value = "test"
    mock_name_extractor.extract_names.return_value = expected_result

    perform_ner(mock_ai, mock_metadata, mock_chapter)

    mock_name_extractor.build_role_script.assert_called_once_with([])
    mock_name_extractor.extract_names.assert_called_once_with("mock ai", mock_chapter, "test", "test narrator")
    mock_chapter.add_names.assert_called_once_with(expected_result)

@patch("lorebinders.build_lorebinder.InstructionType")
@patch("lorebinders.build_lorebinder.name_analyzer")
def test_analyze_names(mock_name_analyzer, mock_instruction_type):
    mock_instruction_type.return_value = "markdown"
    mock_ai = MagicMock()
    mock_ai.model = MagicMock()
    mock_ai.model.absolute_max_tokens = 1000
    mock_metadata = MagicMock()
    mock_metadata.character_traits = []
    mock_chapter = MagicMock()
    mock_name_analyzer.initialize_helpers.return_value = "helper"
    role_scripts = ["test", "data"]
    mock_name_analyzer.build_role_scripts.return_value = role_scripts
    mock_name_analyzer.analyze_names.return_value = {"expected": "result"}

    result = analyze_names(mock_ai, mock_metadata, mock_chapter)

    assert result == {"expected": "result"}
    mock_name_analyzer.initialize_helpers.assert_called_once_with(instruction_type="markdown", absolute_max_tokens=mock_ai.model.absolute_max_tokens, added_character_traits=mock_metadata.character_traits)
    mock_name_analyzer.build_role_scripts.assert_called_once_with(mock_chapter.names, "helper", "markdown")
    mock_name_analyzer.analyze_names.assert_called_once_with(mock_ai, "markdown", role_scripts, mock_chapter)
    mock_chapter.add_analysis.assert_called_once_with(result)

@patch("lorebinders.build_lorebinder.name_summarizer")
def test_summarize_names(mock_name_summarizer):
    mock_ai = "mock_ai"
    mock_binder = {"test": "data"}
    mock_name_summarizer.summarize_names.return_value = {"summary": "test"}

    result = summarize_names(mock_ai, mock_binder)

    assert result == {"summary": "test"}

@patch("lorebinders.build_lorebinder.summarize_names")
def test_summarize(mock_summarize_names):
    mock_ai = "mock_ai"
    mock_book = MagicMock()
    mock_book.binder = {"test": "data"}

    summarize(mock_ai, mock_book)

    mock_summarize_names.assert_called_once_with(mock_ai, mock_book.binder)
    mock_book.update_binder.assert_called_once_with(mock_summarize_names.return_value)


@patch("lorebinders.build_lorebinder.perform_ner")
@patch("lorebinders.build_lorebinder.analyze_names")
@patch("lorebinders.build_lorebinder.data_cleaner.clean_lorebinders")
def test_build_binder(mock_clean_lorebinders, mock_analyze_names, mock_perform_ner):
    chapter = MagicMock()
    chapter.number = 1
    chapter2 = MagicMock()
    chapter2.number = 2
    chapter3 = MagicMock()
    chapter3.number = 3
    chapters =[chapter, chapter2, chapter3]
    mock_book = MagicMock()
    mock_book.chapters = chapters
    mock_book.metadata = MagicMock()
    mock_book.metadata.narrator = "test narrator"
    mock_book.binder = {}
    mock_ner = MagicMock()
    mock_analyzer = MagicMock()
    mock_analysis = [{"test1": "data1"}, {"test2": "data2"}, {"test3": "data3"}]
    mock_analyze_names.side_effect = mock_analysis

    build_binder(mock_ner, mock_analyzer, mock_book.metadata, mock_book)

    mock_perform_ner.assert_has_calls([call(mock_ner, mock_book.metadata, mock_book.chapters[0]), call(mock_ner, mock_book.metadata, mock_book.chapters[1])], call(mock_ner, mock_book.metadata, mock_book.chapters[2]))
    mock_analyze_names.assert_has_calls([call(mock_analyzer, mock_book.metadata, mock_book.chapters[0]), call(mock_analyzer, mock_book.metadata, mock_book.chapters[1])], call(mock_analyzer, mock_book.metadata, mock_book.chapters[2]))
    mock_book.build_binder.assert_has_calls([call(1, {"test1": "data1"}), call(2, {"test2": "data2"}), call(3, {"test3": "data3"})])
    mock_clean_lorebinders.assert_called_once_with({}, "test narrator")


@patch("lorebinders.build_lorebinder.perform_ner")
@patch("lorebinders.build_lorebinder.analyze_names")
@patch("lorebinders.build_lorebinder.data_cleaner.clean_lorebinders")
def test_build_binder_no_narrator(mock_clean_lorebinders, mock_analyze_names, mock_perform_ner):
    chapters =[MagicMock()]
    mock_book = MagicMock()
    mock_book.chapters = chapters
    mock_book.metadata = MagicMock()
    mock_book.metadata.narrator = None
    mock_book.binder = {}
    mock_ner = MagicMock()
    mock_analyzer = MagicMock()

    build_binder(mock_ner, mock_analyzer, mock_book.metadata, mock_book)

    mock_perform_ner.assert_called_once()
    mock_analyze_names.assert_called_once()
    mock_clean_lorebinders.assert_called_once_with({}, "")

@patch("lorebinders.build_lorebinder.convert_book_file")
@patch("lorebinders.build_lorebinder.create_book")
@patch("lorebinders.build_lorebinder.start_ai_initialization.initialize_ai_model_registry")
@patch("lorebinders.build_lorebinder.FileRateLimitHandler")
@patch("lorebinders.build_lorebinder.start_ai_initialization.initialize_ner")
@patch("lorebinders.build_lorebinder.start_ai_initialization.initialize_analyzer")
@patch("lorebinders.build_lorebinder.start_ai_initialization.initialize_summarizer")
@patch("lorebinders.build_lorebinder.build_binder")
@patch("lorebinders.build_lorebinder.summarize")
@patch("lorebinders.build_lorebinder.data_cleaner.final_reshape")
@patch("lorebinders.build_lorebinder.make_pdf.create_pdf")
def test_start(mock_create_pdf, mock_final_reshape, mock_summarize, mock_build_binder, mock_summarizer, mock_analyzer, mock_ner, mockFileRateLimiter, mock_initialize_ai, mock_create_book, mock_convert_book_file):
    book_dict = MagicMock()
    book_dict.user_folder = "test_folder"
    book_dict.title = "Test Book"
    work_base_dir = "/test/work/dir"

    mock_book = MagicMock()
    mock_book.binder = {}
    mock_create_book.return_value = mock_book

    mock_ai_registry = MagicMock()
    mock_initialize_ai.return_value = mock_ai_registry
    mock_provider = MagicMock()
    mock_ai_registry.get_provider.return_value = mock_provider
    mock_rate_handler = MagicMock(spec=FileRateLimitHandler)
    mockFileRateLimiter.return_value = mock_rate_handler
    mock_ner_instance = MagicMock()
    mock_analyzer_instance = MagicMock()
    mock_summarizer_instance = MagicMock()
    mock_ner.return_value = mock_ner_instance
    mock_analyzer.return_value = mock_analyzer_instance
    mock_summarizer.return_value = mock_summarizer_instance

    start(book_dict, work_base_dir)

    mock_convert_book_file.assert_called_once_with(book_dict, work_base_dir)
    mock_create_book.assert_called_once_with(book_dict)
    mock_initialize_ai.assert_called_once_with(JSONFileProviderHandler, "json_files")
    mock_ai_registry.get_provider.assert_called_once_with("OpenAI")
    mockFileRateLimiter.assert_called_once()
    mock_ner.assert_called_once_with(mock_provider, mock_rate_handler)
    mock_analyzer.assert_called_once_with(mock_provider, mock_rate_handler)
    mock_summarizer.assert_called_once_with(mock_provider, mock_rate_handler)
    mock_build_binder.assert_called_once_with(mock_ner_instance, mock_analyzer_instance, book_dict, mock_book)
    mock_summarize.assert_called_once_with(mock_summarizer_instance, mock_book)
    mock_final_reshape.assert_called_once_with({})

    mock_create_pdf.assert_called_once_with(mock_book)
