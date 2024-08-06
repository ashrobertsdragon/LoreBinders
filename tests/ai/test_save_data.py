import pytest
from unittest.mock import call, patch, Mock, MagicMock

from lorebinders.ai.save_data import get_book_by_name, get_file_paths, append_data_to_files, save_progress, MetadataNotSetError

@pytest.fixture
def mock_globals(monkeypatch):
    mock_book = MagicMock()
    mock_book.__repr__ = Mock(return_value="Test Book-Test Author")

    mock_globals = {"Test Book-Test Author": mock_book}
    monkeypatch.setattr("builtins.globals", lambda: mock_globals)
    return mock_globals

def test_get_book_by_name_success(mock_globals):

    result = get_book_by_name("Test Book-Test Author")

    assert isinstance(result, MagicMock)
    assert repr(result) == "Test Book-Test Author"


@patch("lorebinders.ai.save_data.logger")
def test_get_book_by_name_fail(mock_logger, monkeypatch):
    mock_globals = {}
    monkeypatch.setattr("builtins.globals", lambda: mock_globals)
    with pytest.raises(KeyError, match="Book Test Book-Test Author not found."):
        get_book_by_name("Test Book-Test Author")
        mock_logger.error.assert_called_once_with("Book Test Book-Test Author not found.")

@patch("lorebinders.ai.save_data.Path")
def test_get_file_paths_success(mock_path):
    mock_path.return_value = mock_path
    mock_path.__truediv__.side_effect = lambda x: f"/mocked_dir/{x}"

    result = get_file_paths("/mocked_dir")

    assert result["names_file"] == "/mocked_dir/names.json"
    assert result["analysis_file"] == "/mocked_dir/analysis.json"

@patch("lorebinders.ai.save_data.Path")
def test_get_file_paths_user_folder_not_set(mock_path):
    mock_path.return_value = mock_path
    mock_path.__truediv__.side_effect = lambda x: f"/mocked_dir/{x}"

    with pytest.raises(MetadataNotSetError):
        get_file_paths(None)

@patch("lorebinders.ai.save_data.file_handling.append_json_file")

def test_append_data_to_files(mock_append_json_file):
    chapter = Mock()
    chapter.name = "Test Chapter"
    chapter.analysis = {}
    file_paths = {"names_file": "mocked_names_file", "analysis_file": "mocked_analysis_file"}
    chapters = [chapter, chapter]
    
    append_data_to_files(chapters, file_paths)

    mock_append_json_file.assert_has_calls([
        call(chapter.names, file_paths["names_file"]),
        call(chapter.analysis, file_paths["analysis_file"])
    ])
    assert mock_append_json_file.call_count == 4

@patch("lorebinders.ai.save_data.get_file_paths")
@patch("lorebinders.ai.save_data.get_book_by_name")
@patch("lorebinders.ai.save_data.append_data_to_files")
def test_save_progress_success(mock_append_data_to_files, mock_get_book_by_name, mock_get_file_paths):
    mock_book = Mock()
    mock_chapter = Mock()
    mock_book.metadata.user_folder = "mocked_user_folder"
    mock_book.chapters = [mock_chapter, mock_chapter]
    mocked_paths = {"names_file": "mocked_names_file", "analysis_file": "mocked_analysis_file"}

    mock_get_book_by_name.return_value = mock_book
    mock_get_file_paths.return_value = mocked_paths

    result = save_progress("Test Book")

    assert result is True
    
    mock_get_book_by_name.assert_called_once_with("Test Book")
    mock_get_file_paths.assert_called_once_with("mocked_user_folder")
    mock_append_data_to_files.assert_called_once_with(mock_book.chapters, mocked_paths)

@patch("lorebinders.ai.save_data.get_file_paths")
@patch("lorebinders.ai.save_data.get_book_by_name")
@patch("lorebinders.ai.save_data.append_data_to_files")
@patch("lorebinders.ai.save_data.logger")
def test_save_progress_failure(mock_logger, mock_append_data_to_files, mock_get_book_by_name, mock_get_file_paths):
    book_name = "Test Book"
    mock_get_book_by_name.side_effect = KeyError(f"Book {book_name} not found.")

    result = save_progress(book_name)

    assert result is False

    mock_get_book_by_name.assert_called_once_with(book_name)
    mock_get_file_paths.assert_not_called()
    mock_append_data_to_files.assert_not_called()
    mock_logger.error.assert_called_once_with("Failed to save data for book: Test Book")
