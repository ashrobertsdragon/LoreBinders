from unittest.mock import patch

import pytest

from lorebinders.data_cleaner import (
    remove_titles, to_singular, clean_str, clean_list, clean_none_found, ReplaceNarrator, ReshapeDict, FinalReshape, DeduplicateKeys, SortDictionary, clean_lorebinders
)

# Fixtures
@pytest.fixture
def sample_lorebinder():
    return {
        "1": {
            "Characters": {
                "The Narrator": {
                    "Thoughts": "I wonder what will happen.",
                    "Actions": "The narrator walks to the store.",
                },
                "Main Character": {
                    "Thoughts": "I am the main character.",
                    "Actions": "Main character goes home.",
                },
            },
            "Settings": {
                "The Store": {
                    "Description": "It is a small store.",
                    "Location": "Downtown",
                },
            },
        },
        "2": {
            "Characters": {
                "The Narrator": {
                    "Thoughts": "I am narrating.",
                    "Actions": "Narrator goes to the park.",
                },
                "Main Character": {
                    "Thoughts": "I am the main character.",
                    "Actions": "Main character talks to the Narrator.",
                },
            },
            "Settings": {
                "The Park": {
                    "Description": "It is a large park.",
                    "Location": "None found",
                },
            },
        },
    }
@pytest.fixture
def cleaned_dict():
    return {
        "1": {
            "Characters": {
                "The Narrator": {
                    "Thoughts": "I wonder what will happen.",
                    "Actions": "The narrator walks to the store.",
                },
                "Main Character": {
                    "Thoughts": "I am the main character.",
                    "Actions": "Main character goes home.",
                },
            },
            "Settings": {
                "The Store": {
                    "Description": "It is a small store.",
                    "Location": "Downtown",
                },
            },
        },
        "2": {
            "Characters": {
                "The Narrator": {
                    "Thoughts": "I am narrating.",
                    "Actions": "Narrator goes to the park.",
                },
                "Main Character": {
                    "Thoughts": "I am the main character.",
                    "Actions": "Main character talks to the Narrator.",
                },
            },
            "Settings": {
                "The Park": {
                    "Description": "It is a large park."
                },
            },
        },
    }

@pytest.fixture
def deduplicator(sample_lorebinder):
    return DeduplicateKeys()

@pytest.fixture
def reshaper():
    return ReshapeDict()


@pytest.fixture
def final_reshaper():
    return FinalReshape()


@pytest.fixture
def sorter():
    return SortDictionary()


@pytest.fixture
def replace_narrator(sample_lorebinder):
    return ReplaceNarrator(sample_lorebinder)

##############################################################################
# BEGIN TESTS

# test remove_titles
@patch("lorebinders._titles.TITLES")
def test_remove_titles_removes_titles(mock_TITLES):
    mock_TITLES = {"colonel", "mother", "doctor", "king"}
    assert remove_titles("king Harold") == "Harold"
    assert remove_titles("doctor John") == "John"
    assert remove_titles("mother Mary") == "Mary"
    assert remove_titles("colonel Charles") == "Charles"

@patch("lorebinders._titles.TITLES")
def test_remove_titles_removes_uppercase_titles(mock_TITLES):
    mock_TITLES = {"colonel", "mother", "doctor", "king"}
    assert remove_titles("King Harold") == "Harold"
    assert remove_titles("Doctor John") == "John"
    assert remove_titles("Mother Mary") == "Mary"
    assert remove_titles("Colonel Charles") == "Charles"

@patch("lorebinders._titles.TITLES")
def test_remove_titles_does_not_remove_plain_titles(mock_TITLES):
    mock_TITLES = {"colonel", "mother", "doctor", "king"}
    assert remove_titles("King") == "King"
    assert remove_titles("Doctor") == "Doctor"
    assert remove_titles("Mother") == "Mother"
    assert remove_titles("Colonel") == "Colonel"

@patch("lorebinders._titles.TITLES")
def test_remove_titles_does_not_remove_non_matching_names(mock_TITLES):
    mock_TITLES = {"colonel", "mother", "doctor", "king"}
    assert remove_titles("None found") == "None found"
    assert remove_titles("Narrator") == "Narrator"

@patch("lorebinders._titles.TITLES")
def test_remove_titles_raises_typeerror(mock_TITLES):
    mock_TITLES = {"colonel", "mother", "doctor", "king"}
    with pytest.raises(TypeError, match="name must be a string"):
        remove_titles(1)

# test to_singular
def test_to_singular_returns_singular():
    assert to_singular("Loaves") == "loaf"
    assert to_singular("Trophies") == "trophy"
    assert to_singular("Octopi") == "octopus"
    assert to_singular("Quanta") == "quantum"
    assert to_singular("Men") == "man"
    assert to_singular("Dominoes") == "domino"
    assert to_singular("Busses") == "bus"
    assert to_singular("Houses") == "house"
    assert to_singular("Brushes") == "brush"
    assert to_singular("Beaches") == "beach"
    assert to_singular("Booths") == "booth"
    assert to_singular("Sexes") == "sex"
    assert to_singular("Prizes") == "prize"
    assert to_singular("Crates") == "crate"

def test_to_singular_raises_typeerror():
    with pytest.raises(TypeError, match="plural must be a string"):
        to_singular(1)

def test_to_singular_raises_valueerror():
    with pytest.raises(ValueError, match="plural must not be empty"):
        to_singular("")

# Tests for clean_str function
def test_clean_str_removes_none_found():
    assert clean_str("none found") == ""
    assert clean_str("None Found") == ""
    assert clean_str("NONE FOUND") == ""

def test_clean_str_keeps_other_strings():
    assert clean_str("test") == "test"
    assert clean_str("None found here") == "None found here"

# Tests for clean_list function
@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_strings(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test1", ""]
    test_list = ["test1", "none found"]
    assert clean_list(test_list) == ["test1"]
    assert mock_clean_str.call_count == 2
    assert mock_clean_none_found.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_strings_no_changes(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test1", "test2"]
    test_list = ["test1", "test2"]
    assert clean_list(test_list) == test_list
    assert mock_clean_str.call_count == 2
    assert mock_clean_none_found.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_dict_remove_none_found(mock_clean_none_found, mock_clean_str):
    mock_clean_none_found.return_value = {}
    test_list = [{"test": "none found"}]
    assert clean_list(test_list) == []
    assert mock_clean_str.call_count == 0
    assert mock_clean_none_found.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_dict_no_changes(mock_clean_none_found, mock_clean_str):
    mock_clean_none_found.return_value = {"test": "value"}
    test_list = [{"test": "value"}]
    assert clean_list(test_list) == test_list
    assert mock_clean_str.call_count == 0
    assert mock_clean_none_found.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_nested_list_remove_none_found(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test", ""]
    test_list = ["test", ["none found"]]
    assert clean_list(test_list) == ["test"]
    assert mock_clean_str.call_count == 2
    assert mock_clean_none_found.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_nested_list_no_changes(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test", "nested"]
    test_list = ["test", ["nested"]]
    assert clean_list(test_list) == ["test", ["nested"]]
    assert mock_clean_str.call_count == 2
    assert mock_clean_none_found.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_mixed_types_remove_none_found(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test", "nested", ""]
    mock_clean_none_found.return_value = {"key": "value"}
    test_list = ["test", ["nested", "none found"], {"key": "value"}]
    assert clean_list(test_list) == ["test", ["nested"], {"key": "value"}]
    assert mock_clean_str.call_count == 3
    assert mock_clean_none_found.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_none_found")
def test_clean_list_mixed_types_no_changes(mock_clean_none_found, mock_clean_str):
    mock_clean_str.side_effect = ["test", "nested"]
    mock_clean_none_found.return_value = {"key": "value"}
    test_list = ["test", ["nested"], {"key": "value"}]
    assert clean_list(test_list) == test_list
    assert mock_clean_str.call_count == 2
    assert mock_clean_none_found.call_count == 1

# Tests for clean_none_found function
@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_clean_string_values(mock_clean_list, mock_clean_str):
    mock_clean_str.side_effect = ["value", ""]
    test_dict = {"key1": "value", "key2": "none found"}
    assert clean_none_found(test_dict) == {"key1": "value"}
    assert mock_clean_str.call_count == 2
    assert mock_clean_list.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_clean_string_values_no_changes(mock_clean_list, mock_clean_str):
    mock_clean_str.side_effect = ["value1", "value2"]
    test_dict = {"key1": "value1", "key2": "value2"}
    assert clean_none_found(test_dict) == test_dict
    assert mock_clean_str.call_count == 2
    assert mock_clean_list.call_count == 0

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_clean_list_no_items(mock_clean_list, mock_clean_str):
    mock_clean_list.return_value = []
    test_dict = {"key": ["none found"]}
    assert clean_none_found(test_dict) == {}
    assert mock_clean_str.call_count == 0
    assert mock_clean_list.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_clean_list_one_item(mock_clean_list, mock_clean_str):
    mock_clean_list.return_value = ["value1"]
    test_dict = {"key": ["value1", "none found"]}
    assert clean_none_found(test_dict) == {"key": "value1"}
    assert mock_clean_str.call_count == 0
    assert mock_clean_list.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_clean_list_two_items(mock_clean_list, mock_clean_str):
    mock_clean_list.return_value = ["value1", "value2"]
    test_dict = {"key": ["value1", "value2"]}
    assert clean_none_found(test_dict) == test_dict
    assert mock_clean_str.call_count == 0
    assert mock_clean_list.call_count == 1

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_mixed_types_remove_none_found(mock_clean_list, mock_clean_str):
    mock_clean_str.side_effect = ["value3", "value4", "", ""]
    mock_clean_list.side_effect = [["value1", "value2"], [], ["value5"]]
    test_dict = {"key": ["value1", "value2", "none found"], "key2": "value3", "key3": {"key4": "value4"}, "key5": "none found", "key6": {"key7": "none found"}, "key8": ["none found"], "key9": ["none found", "value5"]}
    assert clean_none_found(test_dict) == {"key": ["value1", "value2"], "key2": "value3", "key3": {"key4": "value4"}, "key9": "value5"}
    assert mock_clean_str.call_count == 4
    assert mock_clean_list.call_count == 3

@patch("lorebinders.data_cleaner.clean_str")
@patch("lorebinders.data_cleaner.clean_list")
def test_clean_none_found_mixed_types_no_changes(mock_clean_list, mock_clean_str):
    mock_clean_str.side_effect = ["value3", "value4"]
    mock_clean_list.return_value = ["value1", "value2"]
    test_dict = {"key": ["value1", "value2"], "key2": "value3", "key3": {"key4": "value4"}}
    assert clean_none_found(test_dict) == test_dict
    assert mock_clean_str.call_count == 2
    assert mock_clean_list.call_count == 1

# Tests for DeduplicateKeys class

@patch.object(DeduplicateKeys, '_is_similar_key')
@patch.object(DeduplicateKeys, '_prioritize_keys')
@patch.object(DeduplicateKeys, '_merge_values')
@patch.object(DeduplicateKeys, '_deduplicate_across_dictionaries')
def test_deduplicate_keys_deduplicate_similar_keys(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {"outer": {"key1": "value1", "key2": "value2"}}
    expected_result = {"outer": {"key2": ["value1", "value2"]}}
    mock_is_similar_key.return_value = True
    mock_prioritize_keys.return_value = ("key1", "key2")
    mock_merge_values.return_value = ["value1", "value2"]
    mock_deduplicate_across.return_value = expected_result
    
    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result
    mock_is_similar_key.assert_called_once()
    mock_prioritize_keys.assert_called_once_with("key1", "key2")
    mock_merge_values.assert_called_once_with("value2", "value1")
    mock_deduplicate_across.assert_called_once()

@patch.object(DeduplicateKeys, '_is_similar_key')
@patch.object(DeduplicateKeys, '_prioritize_keys')
@patch.object(DeduplicateKeys, '_merge_values')
@patch.object(DeduplicateKeys, '_deduplicate_across_dictionaries')
def test_deduplicate_keys_deduplicate_non_similar_keys(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {"outer": {"inner1": "value1", "key2": "value2"}}
    expected_result = binder  # No changes expected
    mock_is_similar_key.return_value = False
    mock_deduplicate_across.return_value = expected_result
    
    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result
    mock_is_similar_key.assert_called_once()
    mock_prioritize_keys.assert_not_called()
    mock_merge_values.assert_not_called()
    mock_deduplicate_across.assert_called_once()

@patch.object(DeduplicateKeys, '_is_similar_key')
@patch.object(DeduplicateKeys, '_prioritize_keys')
@patch.object(DeduplicateKeys, '_merge_values')
@patch.object(DeduplicateKeys, '_deduplicate_across_dictionaries')
def test_deduplicate_keys_deduplicate_no_inner(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {"outer1": {"key1": "value1"}, "outer2": {"key2": "value2"}}
    expected_result = binder  # No changes expected
    mock_deduplicate_across.return_value = expected_result
    
    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result
    mock_is_similar_key.assert_not_called()
    mock_prioritize_keys.assert_not_called()
    mock_merge_values.assert_not_called()
    mock_deduplicate_across.assert_called_once()

@pytest.mark.parametrize(
    ("key1", "key2", "is_title", "remove_title", "singular", "expected"),
    [
        ("cat", "cats", [False, False], ["cat", "cats"], ["cat", "cat"], True), # 0
        ("cats", "cat", [False, False], ["cats", "cat"], ["cat", "cat"], True), # 1
        ("cats", "cats", [False, False], ["cats", "cats"], ["cat", "cat"], True), # 2
        (" cat", "cat", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 3
        ("cat ", "cat", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 4
        (" cat ", "cat", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 5
        ("cat", " cat", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 6
        ("cat", "cat ", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 7
        ("cat", " cat ", [False, False], ["cat", "cat"], ["cat", "cat"], True), # 8
        ("cat", "dog", [False, False],  ["cat", "dog"], ["cat", "dog"], False), # 9
        ("cat", "CAT", [False, False],  ["cat", "cat"], ["cat", "cat"], True), # 10
        ("Mr. Smith", "Smith", [False, False], ["smith", "smith"], ["mr. smith", "mr. smith"], True), # 11
        ("Smith", "Mr. Smith", [False, False], ["smith", "smith"], ["mr. smith", "mr. smith"], True), # 12
        ("Mr. Smith", "Mr. Smith", [False, False], ["smith", "smith"], ["mr. smith", "mr. smith"], True), # 13
        ("Mr. Smith", "Smiths", [False, False], ["smith", "smith"], ["mr. smith", "smith"], True), # 14
        ("Smiths", "Mr. Smith", [False, False], ["smith", "smith"], ["smith", "mr. smith"], True), # 15
        ("Mr. Smith", "Mr. Smiths", [False, False], ["smith", "smiths"], ["mr. smith", "mr. smith"], True), # 16
        ("Mr. Smiths", "Mr. Smith", [False, False], ["smith", "smith"], ["mr. smith", "mr. smith"], True), # 17
        ("Mr. Smiths", "Mr. Smiths", [False, False], ["smiths", "smiths"], ["mr. smith", "mr. smith"], True), # 18
        ("Mr. Smiths", "Smith", [False, False], ["smiths", "smith"], ["mr. smith", "smith"], False), # 19
        ("King", "King Edward", [True, False], ["king", "edward"], ["king", "king edward"], True), # 20
        ("King Edward", "King", [False, True], ["edward", "king"], ["king edward", "king"], True), # 21
        ("KiNg", "kInG eDwArD", [True, False], ["king", "edward"], ["king", "king edward"], True), # 22
        ("KiNg eDwArD", "kInG", [False, True], ["edward", "king"], ["king edward", "king"], True), # 23
        ("Queen", "King Edward", [True, False], ["queen", "edward"], ["queen", "king edward"], False), # 24
        ("King Edward", "Queen", [False, True], ["edward", "queen"], ["king edward", "queen"], False), # 25
        ("Red Dragon", "Dragon", [False, False], ["red dragon", "dragon"], ["red dragon", "dragon"], False), # 26
        ("Dragon", "Red Dragon", [False, False], ["dragon", "red dragon"], ["dragon", "red dragon"], False), # 27
        ("dogs", "cats", [False, False], ["dogs", "cats"], ["dog", "cat"], False), # 28,
        ("cats", "dogs", [False, False], ["cats", "dogs"], ["cat", "dog"], False), # 29
        ("Mr. Smith", "Smith Hall", [True, False], ["smith", "metal smith"], ["mr. smith", "metal smith"], True), # 30
        ("Smith Hall", "Mr. Smith", [False, True], ["metal smith", "smith"], ["metal smith", "mr. smith"], True), # 31
        ("Mr. Smith", "blacksmith", [True, False], ["smith", "blacksmith"], ["mr. smith", "blacksmith"], False), # 32
        ("blacksmith", "Mr. Smith", [False, True], ["blacksmith", "smith"], ["blacksmith", "mr. smith"], False), # 33
        ("King", "Kingdom", [True, False], ["king", "kingdom"], ["king", "kingdom"], False), # 34
        ("Kingdom", "King", [False, True], ["kingdom", "king"], ["kingdom", "king"], False), # 35
    ]
)
@patch("lorebinders.data_cleaner.to_singular")
@patch("lorebinders.data_cleaner.remove_titles")
@patch.object(DeduplicateKeys, "_is_title")
def test_deduplicate_keys_is_similar(mock_is_title, mock_remove, mock_to_singular, key1, key2, is_title, remove_title, singular, expected, deduplicator):
    mock_is_title.side_effect = is_title
    mock_remove.side_effect = remove_title
    mock_to_singular.side_effect = singular
    result = deduplicator._is_similar_key(key1, key2)
    assert result == expected