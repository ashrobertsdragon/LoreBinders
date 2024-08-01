import pytest
from unittest.mock import Mock, patch

from lorebinders.ai.rate_limiters.file_rate_limit_handler import FileRateLimitHandler

@pytest.fixture
def MockFileRateLimitHandler():
    return FileRateLimitHandler()

def test_filename(MockFileRateLimitHandler):
    result = MockFileRateLimitHandler._filename("test_model")
    assert result == "test_model_rate_limit_data.json"

@patch("lorebinders.ai.rate_limiters.file_rate_limit_handler.read_json_file")
def test_read(mock_read_json_file, MockFileRateLimitHandler):
    mock_read_json_file.return_value = {"key": "value"}
    MockFileRateLimitHandler._filename = Mock(return_value="test_model_rate_limit_data.json")
    result = MockFileRateLimitHandler.read("test_model")
    assert result == {"key": "value"}
    MockFileRateLimitHandler._filename.assert_called_once_with("test_model")
    mock_read_json_file.assert_called_once_with("test_model_rate_limit_data.json")

@patch("lorebinders.ai.rate_limiters.file_rate_limit_handler.write_json_file")
def test_write(mock_write_json_file, MockFileRateLimitHandler):
    MockFileRateLimitHandler._filename = Mock(return_value="test_model_rate_limit_data.json")
    MockFileRateLimitHandler.write("test_model", {"key": "value"})
    mock_write_json_file.assert_called_once_with({"key": "value"}, "test_model_rate_limit_data.json")
