from unittest.mock import patch

import pytest

from src.lorebinders._decorators import required_string


@pytest.fixture
def valid_input():
    with patch("builtins.input", return_value="Valid Input"):
        yield


@pytest.fixture
def invalid_empty_input():
    with patch("builtins.input", side_effect=["", "Valid Input"]):
        yield


@pytest.fixture
def invalid_whitespace_input():
    with patch("builtins.input", side_effect=["   ", "Valid Input"]):
        yield


@pytest.mark.parametrize(
    "input_fixture",
    [
        ("valid_input", "Valid Input"),
        ("invalid_empty_input", "Valid Input"),
        ("invalid_whitespace_input", "Valid Input"),
    ],
)
def test_decorator(input_fixture):
    input_fixture_name, expected_result = input_fixture
    input_function = locals()[input_fixture_name]

    @required_string
    def test_function():
        return input()

    with input_function:
        assert test_function() == expected_result
