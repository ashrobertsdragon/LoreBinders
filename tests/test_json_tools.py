import pytest
from src.lorebinders.json_tools import MergeJSON


@pytest.fixture
def partial_json():
    return '{"key1": "value1"', '"key2": "value2"}'


@pytest.fixture
def merged_json():
    return '{"key1": "value1", "key2": "value2"}'


@pytest.fixture
def full_json():
    return '{"key1": "value1"}', '{"key2": "value2"}'


def test_merge_success(partial_json, merged_json):
    first_half, second_half = partial_json
    merger = MergeJSON(first_half, second_half)
    merger._find_ends()
    assert merger.merge() == merged_json


def test_merge_failure(full_json):
    first_half, second_half = full_json
    merger = MergeJSON(first_half, second_half)
    merger._find_ends()
    assert merger.merge() == ""


def test_is_valid_json_str_success(merged_json):
    merger = MergeJSON("", "")
    assert merger.is_valid_json_str(merged_json) is True


def test_is_valid_json_str_failure():
    invalid_json_str = '{"key1": "value1", "key2": "value2"'
    merger = MergeJSON("", "")
    assert merger.is_valid_json_str(invalid_json_str) is False


def test_find_ends_success(partial_json):
    first_half, second_half = partial_json
    merger = MergeJSON(first_half, second_half)
    merger._find_ends()
    assert merger.first_end > 0
    assert merger.second_start > 0


def test_find_ends_failure(full_json):
    first_half, second_half = full_json
    merger = MergeJSON(first_half, second_half)
    merger._find_ends()
    assert merger.first_end == 0
    assert merger.second_start == 0


def test_find_full_object_forward():
    partial = '"key2": "value2"}'
    merger = MergeJSON("", "")
    assert merger._find_full_object(partial) == len(partial) - 1


def test_find_full_object_backward():
    partial = '{"key1": "value1"'
    merger = MergeJSON("", "")
    assert (
        merger._find_full_object(partial[::-1], forward=False)
        == len(partial) - 1
    )


def test_find_full_object_failure():
    incomplete = '{"key1": "value1"'
    merger = MergeJSON("", "")
    assert merger._find_full_object(incomplete) == 0
