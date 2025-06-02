from unittest.mock import call, patch

import pytest

from lorebinders.json_tools import is_valid_json_file, json_str_to_dict, repair_json_str, log_merge_warning, build_repair_stub, find_last_full_object, merge_json

@patch("lorebinders.json_tools.file_handling.read_json_file")
@patch("pathlib.Path.exists", return_value=True)
def test_is_valid_json_file(mock_exists, mock_read_json_file):
    mock_read_json_file.return_value = {"key": "value"}
    assert is_valid_json_file("test.json")

@patch("lorebinders.json_tools.repair_json")
def test_json_str_to_dict(mock_repair_json):
    mock_repair_json.return_value = {"key": "value"}
    json_str_to_dict('{"key: "value"}')
    mock_repair_json.assert_called_once_with('{"key: "value"}')


@patch("lorebinders.json_tools.repair_json")
def test_repair_json_str(mock_repair_json):
    mock_repair_json.return_value = '{"key": "value"}'
    repair_json_str("'{\"key: \"value\"}'")
    mock_repair_json.assert_called_once_with("'{\"key: \"value\"}'")


@pytest.fixture
def first_half():
    return '''{
        "level1_key1": {
            "level2_key1": {
                "level3_key1": "value311",
                "level3_key2": "value312",
                "level3_key3": "value313",
                "level3_key4": "value314"
            },
            "level2_key2": {
                "level3_key1": "value321",
                "level3_key2": "value322",
                "level3_key3": "value323"
            },
            "level2_key3": {
                "level3_key1": "value331",
                "level3_key2": "value332",
                "level3_key3": "value333",
                "level3_key4": "value334",
                "level3_key5": "value335"
            }
        },
        "level1_key2": {
            "level2_key1": {
                "level3_key1": "value211",
                "level3_key2": "value212",
                "level3_key3": "value213"
            },
            "level2_key2": {
                "level3_key1": "value221",
                "level3_key2": "value222",
                "level3_key3": "value223",
                "level3_key4": "brokenfh"
    '''

@pytest.fixture
def second_half():
    return '''{
        "level1_key2": {
            "level2_key1": {
                "level3_key1": "value211",
                "level3_key2": "value212",
                "level3_key3": "value213"
            },
            "level2_key2": {
                "level3_key1": "value221",
                "level3_key2": "value222",
                "level3_key3": "value223",
                "level3_key4": "value224"
            },
            "level2_key3": {
                "level3_key1": "value231",
                "level3_key2": "value232",
                "level3_key3": "value233"
            },
            "level2_key4": {
                "level3_key1": "value241",
                "level3_key2": "value242",
                "level3_key3": "value243"
            }
        },
        "level1_key3": {
            "level2_key1": {
                "level3_key1": "value311",
                "level3_key2": "value312",
                "level3_key3": "value313",
                "level3_key4": "value314",
                "level3_key5": "value315"
            },
            "level2_key2": {
                "level3_key1": "value321",
                "level3_key2": "value322",
                "level3_key3": "value323",
                "level3_key4": "value324"
            },
            "level2_key3": {
                "level3_key1": "value331",
                "level3_key2": "value332",
                "level3_key3": "value333"
            }
        }
    }
    '''

@pytest.fixture
def full_json_object():
    return '''{
        "level1_key1": {
            "level2_key1": {
                "level3_key1": "value311",
                "level3_key2": "value312",
                "level3_key3": "value313",
                "level3_key4": "value314"
            },
            "level2_key2": {
                "level3_key1": "value321",
                "level3_key2": "value322",
                "level3_key3": "value323"
            },
            "level2_key3": {
                "level3_key1": "value331",
                "level3_key2": "value332",
                "level3_key3": "value333",
                "level3_key4": "value334",
                "level3_key5": "value335"
            }
        },
        "level1_key2": {
            "level2_key1": {
                "level3_key1": "value211",
                "level3_key2": "value212",
                "level3_key3": "value213"
            },
            "level2_key2": {
                "level3_key1": "value221",
                "level3_key2": "value222",
                "level3_key3": "value223",
                "level3_key4": "value224"
            },
            "level2_key3": {
                "level3_key1": "value231",
                "level3_key2": "value232",
                "level3_key3": "value233"
            },
            "level2_key4": {
                "level3_key1": "value241",
                "level3_key2": "value242",
                "level3_key3": "value243"
            }
        },
        "level1_key3": {
            "level2_key1": {
                "level3_key1": "value311",
                "level3_key2": "value312",
                "level3_key3": "value313",
                "level3_key4": "value314",
                "level3_key5": "value315"
            },
            "level2_key2": {
                "level3_key1": "value321",
                "level3_key2": "value322",
                "level3_key3": "value323",
                "level3_key4": "value324"
            },
            "level2_key3": {
                "level3_key1": "value331",
                "level3_key2": "value332",
                "level3_key3": "value333"
            }
        }
    }
    '''

def test_build_repair_stub():
    first_part = '{"test": "value"},'
    second_part = '"value2"'

    result = build_repair_stub(first_part, second_part)

    assert result == 'First part: {"test": "value"},\nhas no complete object\nSecond part: "value2"'

@patch("lorebinders.json_tools.logger")
@patch("lorebinders.json_tools.build_repair_stub")
def test_log_merge_warning(mock_build_repair_stub, mock_logger):
    first_part = '{"test": "value"},'
    second_part = '"value2"'

    mock_build_repair_stub.return_value = 'First part: {"test": "value"},\nhas no complete object\nSecond part: "value2"'
    log_merge_warning(first_part, second_part)
    assert mock_logger.warn('Could not combine.\nFirst part: {"test": "value"},\nhas no complete object\nSecond part: "value2"')

@pytest.mark.parametrize(
    "string, expected",
    [
        ('{"a": {"c": 3, "d": 4}}', 21),
        ('{"a":1,"b":{"c":3}', 17),
        ('{"a": 1, "b": {"c": 3', 0),
        ('{"a": {"b": 1}, "c": 2', 13),
        ('{"a": {"b": 1, 2', 0),
        ('{"a": {"b": 1, "c": 2}, {"d": 3}', 31),
        ('{"a": {"b": 1, "c": 2}, {"d": 3', 21)
    ]
)
def test_find_last_full_object(string, expected, first_half):
    first_result = find_last_full_object(first_half)

    parametrized_results = find_last_full_object(string)
    assert first_result == 679
    assert parametrized_results == expected

@patch("lorebinders.json_tools.find_last_full_object")
@patch("lorebinders.json_tools.log_merge_warning")
def test_merge_json_success(mock_log_merge_warning, mock_find_last_full_object, first_half, second_half, full_json_object):
    mock_find_last_full_object.return_value = 679

    result = merge_json(first_half, second_half)

    assert result == full_json_object
    mock_log_merge_warning.assert_not_called()
    mock_find_last_full_object.assert_called_once_with(first_half)


@patch("lorebinders.json_tools.find_last_full_object")
@patch("lorebinders.json_tools.log_merge_warning")
def test_merge_json_failure(mock_log_merge_warning, mock_find_last_full_object):
    first_half = '{"test": "value"'
    second_half = '"value2"}'
    mock_find_last_full_object.return_value = 0

    result = merge_json(first_half, second_half)

    assert result == ""
    mock_log_merge_warning.assert_called_once_with(first_half, second_half)
    mock_find_last_full_object.assert_called_once_with(first_half)
