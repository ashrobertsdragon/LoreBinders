import os
from unittest.mock import MagicMock, patch

import pytest

from lorebinders.book import Book, Chapter
from lorebinders.book_dict import BookDict
from lorebinders.ai.ai_models.json_file_model_handler import JSONFileProviderHandler
from lorebinders.ai.rate_limiters.file_rate_limit_handler import FileRateLimitHandler
from lorebinders.build_lorebinder import (
    convert,
    convert_book_file,
    create_book,
    create_folder,
    create_limited_metadata,
    add_txt_filename,
    create_user,
    create_user_folder,
    build_binder,
    initialize_name_tools,
    start,
    initialize_ai_model_registry,
    summarize_names,
    perform_ner,
    analyze_names,
    summarize,
    make_pdf
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

def test_perform_ner(mock_ner, mock_metadata, mock_chapter):
    perform_ner(mock_ner, mock_metadata, mock_chapter)

    mock_ner.initialize_chapter.assert_called_once_with(mock_metadata, mock_chapter)
    mock_ner.build_role_script.assert_called_once()
    mock_ner.extract_names.assert_called_once()
    mock_chapter.add_names.assert_called_once()

def test_analyze_names(mock_analyzer, mock_metadata, mock_chapter):
    analyze_names(mock_analyzer, mock_metadata, mock_chapter)

    mock_analyzer.initialize_chapter.assert_called_once_with(mock_metadata, mock_chapter)
    mock_analyzer.build_role_script.assert_called_once()
    mock_analyzer.analyze_names.assert_called_once()
    mock_chapter.add_analysis.assert_called_once()

def test_summarize_names(mock_summarizer):
    mock_binder = {"test": "data"}
    mock_summarizer.summarize_names.return_value = {"summary": "test"}

    result = summarize_names(mock_summarizer, mock_binder)

    mock_summarizer.build_role_script.assert_called_once()
    mock_summarizer.summarize_names.assert_called_once_with(mock_binder)
    assert result == {"summary": "test"}

@patch('lorebinders.build_lorebinder.NameExtractor')
@patch('lorebinders.build_lorebinder.NameAnalyzer')
@patch('lorebinders.build_lorebinder.NameSummarizer')
def test_initialize_name_tools(mock_NameSummarizer, mock_NameAnalyzer, mock_NameExtractor):
    mock_provider = MagicMock()
    mock_rate_limit_handler = MagicMock()

    ner, analyzer, summarizer = initialize_name_tools(mock_provider, mock_rate_limit_handler)

    mock_NameExtractor.assert_called_once_with(mock_provider, mock_rate_limit_handler)
    mock_NameAnalyzer.assert_called_once_with(mock_provider, mock_rate_limit_handler)
    mock_NameSummarizer.assert_called_once_with(mock_provider, mock_rate_limit_handler)

    assert isinstance(ner, MagicMock)
    assert isinstance(analyzer, MagicMock)
    assert isinstance(summarizer, MagicMock)

def test_summarize(mock_book, mock_summarizer):
    mock_binder = {"test": "data"}
    mock_summarizer.summarize_names.return_value = {"summary": "test"}
    mock_book.binder = mock_binder

    summarize(mock_book, mock_summarizer)

    mock_summarizer.summarize_names.assert_called_once_with(mock_binder)
    mock_book.update_binder.assert_called_once_with({"summary": "test"})


@patch('os.path.exists')
@patch('os.makedirs')
def test_create_folder(mock_makedirs, mock_exists):
    user = "test_user"
    base_dir = "work"
    expected_folder = os.path.join(base_dir, user)

    mock_exists.return_value = False
    result = create_folder(user, base_dir)

    assert result == expected_folder
    mock_makedirs.assert_called_once_with(expected_folder, exist_ok=True)


def test_create_user_converts_author_to_user_format():
    author = "John Doe"
    expected_user = "John_Doe"

    assert create_user(author) == expected_user


@patch('lorebinders.build_lorebinder.create_folder')
def test_create_user_folder(mock_create_folder):
    author = "Jane Smith"
    work_dir = "work"
    expected_folder = os.path.join(work_dir, "Jane_Smith")

    mock_create_folder.return_value = expected_folder
    result = create_user_folder(author, work_dir)

    assert result == expected_folder
    mock_create_folder.assert_called_once_with("Jane_Smith", work_dir)


def test_add_txt_filename():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    add_txt_filename(book_dict, book_dict.book_file)

    assert book_dict.txt_file == "test_file.txt"

@patch("lorebinders.build_lorebinder.convert_file")
def test_convert(mock_convert_file):
    file_path = "test_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    convert(file_path, limited_metadata)

    mock_convert_file.assert_called_once_with(file_path, limited_metadata)


def test_convert_book_file_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"

    with pytest.raises(Exception):
        convert_book_file(book_dict)


def test_create_book_raises_exception_author_missing():
    book_dict = MagicMock()
    book_dict.author = None
    book_dict.title = "Test Title"

    with pytest.raises(Exception):
        create_book(book_dict)


def test_create_limited_metadata():
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"

    assert create_limited_metadata(book_dict) == {
        "title": "Test Title",
        "author": "John Doe",
    }



@patch('lorebinders.build_lorebinder.create_user_folder')
@patch('lorebinders.build_lorebinder.convert')
def test_convert_book_file(mock_convert, mock_create_user_folder):
    book_dict = MagicMock()
    book_dict.author = "John Doe"
    book_dict.title = "Test Title"
    book_dict.book_file = "test_file.pdf"
    work_dir = "work"

    mock_create_user_folder.return_value = "/mock/user/folder"

    convert_book_file(book_dict, work_dir)

    mock_create_user_folder.assert_called_once_with("John Doe", work_dir)
    mock_convert.assert_called_once()
    assert book_dict.txt_file == "test_file.txt"

def test_convert_raises_exception_file_does_not_exist():
    file_path = "non_existent_file.txt"
    limited_metadata = {"title": "Test Title", "author": "John Doe"}

    with pytest.raises(Exception):
        convert(file_path, limited_metadata)


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


def test_initialize_ai_model_registry():
    mock_provider_registry = MagicMock()
    mock_provider_registry.return_value.registry = "mock_registry"

    result = initialize_ai_model_registry(mock_provider_registry, "arg1", kwarg1="value1")

    assert result == "mock_registry"
    mock_provider_registry.assert_called_once_with("arg1", kwarg1="value1")

@patch("lorebinders.build_lorebinder.convert_book_file")
@patch("lorebinders.build_lorebinder.create_book")
@patch("lorebinders.build_lorebinder.initialize_ai_model_registry")
@patch("lorebinders.build_lorebinder.initialize_name_tools")
@patch("lorebinders.build_lorebinder.build_binder")
@patch("lorebinders.build_lorebinder.summarize")
@patch("lorebinders.build_lorebinder.make_pdf.create_pdf")
@patch("lorebinders.build_lorebinder.FileRateLimitHandler")
def test_start(mock_FileRateLimitHandler, mock_create_pdf, mock_summarize, mock_build_binder, mock_initialize_name_tools,
               mock_initialize_ai_model_registry, mock_create_book, mock_convert_book_file):
    book_dict = MagicMock()
    book_dict.user_folder = "test_folder"
    book_dict.title = "Test Book"
    work_base_dir = "/test/work/dir"

    mock_book = MagicMock()
    mock_create_book.return_value = mock_book

    mock_ai_registry = MagicMock()
    mock_initialize_ai_model_registry.return_value = mock_ai_registry
    mock_provider = MagicMock()
    mock_ai_registry.get_provider.return_value = mock_provider
    mock_rate_handler = MagicMock(spec=FileRateLimitHandler)
    mock_FileRateLimitHandler.return_value = mock_rate_handler
    mock_ner, mock_analyzer, mock_summarizer = MagicMock(), MagicMock(), MagicMock()
    mock_initialize_name_tools.return_value = (mock_ner, mock_analyzer, mock_summarizer)

    start(book_dict, work_base_dir)

    mock_convert_book_file.assert_called_once_with(book_dict, work_base_dir)
    mock_create_book.assert_called_once_with(book_dict)
    mock_initialize_ai_model_registry.assert_called_once_with(JSONFileProviderHandler, "json_files")
    mock_ai_registry.get_provider.assert_called_once_with("OpenAI")
    mock_initialize_name_tools.assert_called_once_with(mock_provider, mock_rate_handler)
    mock_build_binder.assert_called_once_with(mock_book, mock_ner, mock_analyzer)
    mock_summarize.assert_called_once_with(mock_book, mock_summarizer)

    mock_create_pdf.assert_called_once_with("test_folder", "Test Book")


def test_build_binder(mock_book, mock_ner, mock_analyzer):
    mock_book.chapters = [MagicMock(spec=Chapter) for _ in range(3)]
    mock_book.metadata = MagicMock(spec=BookDict)
    mock_perform_ner = MagicMock()
    mock_analyze_names = MagicMock()

    with patch("lorebinders.build_lorebinder.perform_ner", mock_perform_ner), patch("lorebinders.build_lorebinder.analyze_names", mock_analyze_names):
        build_binder(mock_book, mock_ner, mock_analyzer)

        assert mock_perform_ner.call_count == 3
        assert mock_analyze_names.call_count == 3
