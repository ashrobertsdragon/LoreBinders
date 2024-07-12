from unittest.mock import call, patch

import pytest

from lorebinders._decorators import required_string

@pytest.fixture
def decorated_input_text():
    @required_string
    def input_text():
        return input("Enter text: ")
    return input_text

@patch('builtins.input', side_effect=["John Doe"])
def test_decorated_function_returns_non_empty_string(mock_input, decorated_input_text):
    result = decorated_input_text()
    assert result == "John Doe"
    mock_input.assert_called_once_with("Enter text: ")

@patch('builtins.print')
@patch('builtins.input', side_effect=["", "Valid Input"])
def test_decorated_function_handles_empty_string(mock_input, mock_print, decorated_input_text):
    result = decorated_input_text()
    assert result == "Valid Input"
    mock_print.assert_called_once_with("text is required.")
    assert mock_input.call_count == 2
    mock_input.assert_has_calls([call("Enter text: "), call("Enter text: ")])

@patch('builtins.input', side_effect=["Special!@#$%^&*Chars"])
def test_decorated_function_handles_special_characters(mock_input, decorated_input_text):
    result = decorated_input_text()
    assert result == "Special!@#$%^&*Chars"
    mock_input.assert_called_once_with("Enter text: ")

@patch('builtins.input')
def test_decorated_function_handles_large_string_inputs(mock_input, decorated_input_text):
    large_string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    mock_input.return_value = large_string
    result = decorated_input_text()
    assert result == large_string
    assert isinstance(result, str)
    mock_input.assert_called_once_with("Enter text: ")

@patch('builtins.print')
@patch('builtins.input', side_effect=[" ", "\t", "\n", "Valid Input"])
def test_decorated_function_handles_whitespace_inputs(mock_input, mock_print, decorated_input_text):
    result = decorated_input_text()
    assert result == "Valid Input"
    assert mock_print.call_count == 3
    mock_print.assert_has_calls([call("text is required.")] * 3)
    assert mock_input.call_count == 4
    mock_input.assert_has_calls([call("Enter text: ")] * 4)
