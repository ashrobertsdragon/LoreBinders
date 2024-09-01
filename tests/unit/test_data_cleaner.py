from unittest.mock import call, patch, Mock

import pytest

from lorebinders.data_cleaner import (
    final_reshape, remove_titles, to_singular, clean_str, clean_list, clean_none_found, ReplaceNarrator, reshape_dict, DeduplicateKeys, sort_dictionary, clean_lorebinders
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
def test_deduplicate_keys_deduplicate_no_nested_dict(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {"key1": "value1", "key2": "value2"}
    mock_deduplicate_across.return_value = binder
    result = deduplicator.deduplicate(binder)

    assert result == binder
    mock_is_similar_key.assert_not_called()
    mock_prioritize_keys.assert_not_called()
    mock_merge_values.assert_not_called()
    mock_deduplicate_across.assert_called_once()

@patch.object(DeduplicateKeys, '_is_similar_key')
@patch.object(DeduplicateKeys, '_prioritize_keys')
@patch.object(DeduplicateKeys, '_merge_values')
@patch.object(DeduplicateKeys, '_deduplicate_across_dictionaries')
def test_deduplicate_keys_deduplicate_mixed_types_nested_dict(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {"key1": "value1", "key2": {"key3": "value3", "similar_key": "value4"}}
    expected_binder = {"key1": "value1", "key2": {"key3": ["value3", "value4"]}}
    mock_deduplicate_across.return_value = expected_binder
    mock_is_similar_key.return_value = True
    mock_prioritize_keys.return_value = ("similar_key", "key3")
    mock_merge_values.return_value = ["value3", "value4"]

    result = deduplicator.deduplicate(binder)

    assert result == expected_binder
    mock_is_similar_key.assert_called_once()
    mock_prioritize_keys.assert_called_once_with("key3", "similar_key")
    mock_merge_values.assert_called_once_with("value3", "value4")
    mock_deduplicate_across.assert_called_once()

@patch.object(DeduplicateKeys, '_is_similar_key')
@patch.object(DeduplicateKeys, '_prioritize_keys')
@patch.object(DeduplicateKeys, '_merge_values')
@patch.object(DeduplicateKeys, '_deduplicate_across_dictionaries')
def test_deduplicate_keys_deduplicate_skip_already_deduplicated(mock_deduplicate_across, mock_merge_values, mock_prioritize_keys, mock_is_similar_key, deduplicator):
    binder = {
        "outer_key": {
            "cats": [1, 2, 3],
            "cat":  [4],
            "dogs": [5],
            "dog":  [6],
        }
    }
    expected_result = {
        "outer_key": {
            "cats": [1, 2, 3, 4],
            "dogs": [5, 6],
        }
    }
    expected_is_similar_calls = [
        call("cats", "cat"),
        call("cats", "dogs"),
        call("cats", "dog"),
        call("dogs", "dog")
    ]
    mock_deduplicate_across.return_value = expected_result
    mock_is_similar_key.side_effect = [
        True,  # cats vs cat
        False, # cats vs dogs
        False, # cats vs dog
        True   # dogs vs dog
    ]
    mock_prioritize_keys.side_effect = [
        ("cat", "cats"), # cats vs cat
        ("dog", "dogs"), # dogs vs dog
    ]
    mock_merge_values.side_effect = [
        [1, 2, 3, 4], # merge cats and cat
        [5, 6]        # merge dogs and dog
    ]

    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result
    mock_is_similar_key.assert_has_calls(expected_is_similar_calls)
    assert mock_is_similar_key.call_count == 4
    assert mock_prioritize_keys.call_count == 2
    assert mock_merge_values.call_count == 2
    mock_deduplicate_across.assert_called_once()

@pytest.mark.parametrize(
    ("key1", "key2", "is_titles", "expected"),
    [
        ("short", "longer", [False, False], ("short", "longer")),
        ("longer", "short", [False, False], ("short", "longer")),
        ("King", "King Edward", [True, False], ("King Edward", "King")),
        ("King Edward", "King", [False, True], ("King Edward", "King")),
        ("Short", "longer", [False, False], ("Short", "longer")),
        ("short", "Longer", [False, False], ("short", "Longer")),
        ("", "test", [False, False], ("", "test")),
        ("test", "", [False, False], ("", "test")),
        ("", "King Edward", [False, False], ("", "King Edward")),
        ("King Edward", "", [False, False], ("", "King Edward")),
        ("", "", [False, False], ("", "")),
        ("test", "test", [False, False], ("test", "test")),
        ("test1", "test2", [False, False], ("test1", "test2")),
        ("king", "queen", [True, True], ("king", "queen")),
    ]
)
@patch.object(DeduplicateKeys, "_is_title")
def test_deduplicate_keys_prioritize_keys(mock_is_title, key1, key2, is_titles, expected, deduplicator):
    mock_is_title.side_effect = is_titles
    result = deduplicator._prioritize_keys(key1, key2)
    assert result == expected

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

@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("king", True),
        ("queen", True),
        ("mr", True),
        ("mrs", True),
        ("King", True),
        ("Queen", True),
        ("Mr", True),
        ("Mrs", True),
        ("kingdom", False),
        ("test", False),
        ("", False),
        (" ", False),
        ("king edward", False),
        ("queen elizabeth", False),
        ("mr smith", False),
        ("mrs smith", False)
    ]
)
@patch("lorebinders._titles.TITLES")
def test_deduplicate_keys_is_title(mock_titles,case, expected, deduplicator):
    mock_titles = {"king", "queen", "mr", "mrs"}
    result = deduplicator._is_title(case)
    assert result == expected

@pytest.mark.parametrize(
    "summaries, expected_result, mock_return_value, mock_call_count",
    [
        (
            {
                "Characters": {"Name1": {"Chapter1": "Details1"}, "Name2": {"Chapter1": "Details2"}}
            },
            {
                "Characters": {"Name1": {"Chapter1": "Details1"}, "Name2": {"Chapter1": "Details2"}}
            },
            None, 0 # case 0
        ),
        (
            {
                "Characters": {},
                "Category1": {"Name1": {"Chapter1": "Details1"}},
                "Category2": {"Name2": {"Chapter2": "Details2"}}
            },
            {
                "Characters": {},
                "Category1": {"Name1": {"Chapter1": "Details1"}},
                "Category2": {"Name2": {"Chapter2": "Details2"}}
            },
            None, 0 # case 1
        ),
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter1": {"Details": "New Details"}}}},
            {"Characters": {"Name1": {"Chapter1": {"Details": ["Existing Details", "New Details"]}}}},
            {"Details": ["Existing Details", "New Details"]},
            1 # case 2
        ),
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter2": {"Details": "New Chapter Details"}}}},
            {
                "Characters": {
                    "Name1": {
                        "Chapter1": {"Details": "Existing Details"},
                        "Chapter2": {"Details": "New Chapter Details"}
                    }
                }
            },
            None, 0 # case 3
        ),
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter2": "Non-dict Details"}}},
            {"Characters": {
                "Name1": {"Chapter1": {"Details": "Existing Details"}, "Chapter2": {"Also": "Non-dict Details"}}}},
            None, 0 # case 4
        )
    ]
)
@patch.object(DeduplicateKeys, "_merge_values")
def test_deduplicate_across_dictionaries(mock_merge_values, deduplicator, summaries, expected_result, mock_return_value, mock_call_count):
    mock_merge_values.return_value = mock_return_value
    result = deduplicator._deduplicate_across_dictionaries(summaries)
    assert result == expected_result
    assert mock_merge_values.call_count == mock_call_count

@patch.object(DeduplicateKeys, "_merge_values")
def test_deduplicate_across_dictionaries_merge_values_called_with_correct_args(mock_merge_values, deduplicator):
    summaries = {
        "Characters": {"Name1": {"Chapter1": "Existing Details"}},
        "Category1": {"Name1": {"Chapter1": "New Details"}}
    }
    mock_merge_values.return_value = ["Existing Details", "New Details"]
    deduplicator._deduplicate_across_dictionaries(summaries)
    mock_merge_values.assert_called_once_with("Existing Details", "New Details")

@patch.object(DeduplicateKeys, "_merge_values")
def test_deduplicate_across_dictionaries_keys_deleted(mock_merge_values, deduplicator):
    mock_merge_values.side_effect = [["Details1", "Details3"], ["Details2", "Details4"]]
    summaries = {
        "Characters": {"Name1": {"Chapter1": "Details1"}, "Name2": {"Chapter2": "Details2"}},
        "Category1": {"Name1": {"Chapter1": "Details3"}},
        "Category2": {"Name2": {"Chapter2": "Details4"}}
    }
    result = deduplicator._deduplicate_across_dictionaries(summaries)
    assert "Category1" not in result
    assert "Category2" not in result
    assert "Details3" in result["Characters"]["Name1"]["Chapter1"]
    assert "Details4" in result["Characters"]["Name2"]["Chapter2"]

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_two_dicts(mock_chainmap, deduplicator):
    mock_chainmap.return_value = {"key1": "value1", "key2": "value2"}
    result = deduplicator._merge_values({"key1": "value1"}, {"key2": "value2"})
    assert result == {"key1": "value1", "key2": "value2"}

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_two_lists(mock_chainmap, deduplicator):
    result = deduplicator._merge_values([1, 2], [3, 4])
    assert result == [1, 2, 3, 4]
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_list_and_dict_no_overlap(mock_chainmap, deduplicator):
    mock_chainmap.return_value = {"a": 1, "b": 2, "c": 3}
    result = deduplicator._merge_values([{"a": 1}, "test"], {"b": 2, "c": 3})
    assert result == [{"a": 1, "b": 2, "c": 3}, "test"]

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_list_and_dic_overlap(mock_chainmap, deduplicator):
    mock_chainmap.return_value = {"a": 1, "b": 2, "c": 3}
    result = deduplicator._merge_values([{"a": 1}, "test"], {"a": 1, "b": 2, "c": 3})
    assert result == [{"a": 1, "b": 2, "c": 3}, "test"]

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_invalid_type_with_dict(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, {"key": "value"})
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_invalid_type_with_list(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, [1, 2])
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_invalid_type_with_string(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, "string_value")
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_dict_with_invalid_type(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, {"key": "value"})
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_list_with_invalid_type(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, [1, 2])
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_string_with_invalid_type(mock_chainmap, deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, "string_value")
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_dictionary_and_list(mock_chainmap, deduplicator):
    dict_value = {"key1": "value1"}
    list_value = ["item1", "item2"]
    result = deduplicator._merge_values(dict_value, list_value)
    assert result == {"key1": "value1", "Also": ["item1", "item2"]}
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_recursive(mock_chainmap, deduplicator):
    dict_value = {"Also": "value1"}
    list_value = ["item1", "item2"]
    result = deduplicator._merge_values(dict_value, list_value)
    assert result == {"Also": ["item1", "item2", "value1"]}
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_two_strings_return_list(mock_chainmap, deduplicator):
    value1 = "string1"
    value2 = "string2"

    result = deduplicator._merge_values(value1, value2)

    assert result == [value1, value2]
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_string_with_list(mock_chainmap, deduplicator):
    deduplicator = deduplicator._merge_values("item1", ["item2"])
    assert deduplicator == ["item2", "item1"]
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_list_with_string(mock_chainmap, deduplicator):
    result = deduplicator._merge_values("string", ["item1", "item2"])
    assert result == ["item1", "item2", "string"]
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_dict_with_string(mock_chainmap, deduplicator):
    dict1 = {"key1": "value1"}
    string2 = "string value"
    expected_result = {"key1": "value1", "Also": "string value"}

    result = deduplicator._merge_values(dict1, string2)

    assert result == expected_result 
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_dict_with_string_key(mock_chainmap, deduplicator):
    original_dict = {"key1": "value1"}
    result = deduplicator._merge_values(original_dict, "key1")
    assert result == original_dict
    {"key1": "value1"}
    mock_chainmap.assert_not_called()

@patch("lorebinders.data_cleaner.ChainMap")
def test_deduplicate_keys_merge_values_merge_dict_with_string_value(mock_chainmap, deduplicator):
    original_dict = {"key1": "value1"}
    result = deduplicator._merge_values(original_dict, "value1")
    assert result == {"key1": "value1", "Also": "value1"}
    mock_chainmap.assert_not_called()

def test_reshape_dict_multiple_chapters_categories():
    binder = {
        "Chapter1": {
            "category1": {
                "name1": "details1",
                "name2": "details2"
            },
            "category2": {
                "name3": "details3"
            }
        },
        "Chapter2": {
            "category1": {
                "name1": "details4"
            }
        }
    }
    expected_output = {
        "Category1": {
            "name1": {"Chapter1": "details1", "Chapter2": "details4"},
            "name2": {"Chapter1": "details2"}
        },
        "Category2": {
            "name3": {"Chapter1": "details3"}
        }
    }
    assert reshape_dict(binder) == expected_output

def test_reshape_dict_nested_structures():
    binder = {
        "Chapter1": {
            "category1": {
                "name1": {"sub_name1": "sub_details1"},
                "name2": {"sub_name2": "sub_details2"}
            }
        }
    }
    expected_output = {
        "Category1": {
            "name1": {"Chapter1": {"sub_name1": "sub_details1"}},
            "name2": {"Chapter1": {"sub_name2": "sub_details2"}}
        }
    }
    reshaped_data = reshape_dict(binder)
    assert reshaped_data == expected_output

def test_reshape_dict_empty_input():
    binder = {}
    expected_output = {}
    assert reshape_dict(binder) == expected_output


def test_final_reshape():
    binder = {
        "Characters": {
            "Alice": {
                1: {"trait1": "detail1"},
                2: {"trait2": "detail2"}
            }
        },
        "Settings": {
            "Forest": {
                1: {"traitA": "detailA"},
                2: {"traitB": "detailB"}
            }
        }
    }
    expected_output = {
        "Characters": {
            "Alice": {
                "trait1": {1: "detail1"},
                "trait2": {2: "detail2"}
            }
        },
        "Settings": {
            "Forest": {
                "traitA": {1: "detailA"},
                "traitB": {2: "detailB"}
            }
        }
    }
    assert final_reshape(binder) == expected_output

def test_final_reshape_empty_binder():
    binder = {}
    expected_output = {}
    assert final_reshape(binder) == expected_output

def test_final_reshape_handles_empty_characters_or_settings():
    binder = {
        "Characters": {},
        "Settings": {},
        "Other": {"name1": "Test"}
    }
    expected_output = {
        "Characters": {},
        "Settings": {},
        "Other": {"name1": "Test"}
    }
    assert final_reshape(binder) == expected_output

def test_final_reshape_non_dict_traits_raises_error():
    binder = {
        "Characters": {
            "Dave": {
                1: "simple_trait"
            }
        }
    }
    with pytest.raises(AttributeError):
        final_reshape(binder)

def test_final_reshape_returns_unchanged_dict_when_no_characters_or_settings():
    binder = {"Other": {"name1": "Test"}}
    assert final_reshape(binder) == binder

def test_sort_dictionary_sorts_nested_dict():
    binder = {
        "outer_key": {
            "middle_key": {3: "c", 1: "a", 2: "b"}
        }
    }
    expected = {
        "outer_key": {
            "middle_key": {"1": "a", "2": "b", "3": "c"}
        }
    }
    assert sort_dictionary(binder) == expected

def test_sort_dictionary_returns_same_structure():
    binder = {
        "outer_key1": {
            "middle_key1": {1: "a"}
        },
        "outer_key2": {
            "middle_key2": {2: "b"}
        }
    }
    result = sort_dictionary(binder)
    assert set(result.keys()) == set(binder.keys())
    for outer_key in binder:
        assert set(result[outer_key].keys()) == set(binder[outer_key].keys())

def test_sort_dictionary_handles_multiple_levels():
    binder = {
        "outer_key": {
            "middle_key": {
                1: {"inner_key": {3: "c", 1: "a", 2: "b"}}
            }
        }
    }
    expected = {
        "outer_key": {
            "middle_key": {
                "1": {"inner_key": {1: "a", 2: "b", 3: "c"}}
            }
        }
    }
    assert sort_dictionary(binder) == expected

def test_sort_dictionary_handles_empty_dicts():
    binder = {}
    assert sort_dictionary(binder) == {}

def test_sort_dictionary_raises_type_error_non_integer_keys():
    binder = {
        "outer_key": {
            "middle_key": {"a": "value"}
        }
    }
    with pytest.raises(TypeError):
        sort_dictionary(binder)

def test_sort_dictionary_raises_attribute_error_non_dict_inner():
    binder = {
        "outer_key": {
            "middle_key": ["not", "a", "dict"]
        }
    }
    with pytest.raises(AttributeError):
        sort_dictionary(binder)

def test_sort_dictionary_handles_mixed_types():
    binder = {
        'a': {1: 'value', 'b': 2},
        'c': {'x': 5, 'y': 6}
    }
    with pytest.raises(TypeError):
        sort_dictionary(binder)

def test_sort_dictionary_handles_large_dictionaries_efficiently():
    large_binder = {
        'a': {f'{i}01': {i: f'value_{i}01'} for i in range(1000, 0, -1)},
        'b': {f'{i}01': {i: f'value_{i}01'} for i in range(2000, 1000, -1)}
    }
    large_expected_result = {
        'a': {f'{i}01': {str(i): f'value_{i}01'} for i in range(1, 1001)},
        'b': {f'{i}01': {str(i): f'value_{i}01'} for i in range(1001, 2001)}
    }
    large_result = sort_dictionary(large_binder)
    assert large_result == large_expected_result

# test ReplaceNarrator
def test_replace_narrator_init():
    binder = {"key": "value"}
    instance = ReplaceNarrator(binder)
    assert instance._binder == binder

@patch("lorebinders.data_cleaner.re.sub")
def test_replace_narrator_replace_str(mock_sub,replace_narrator):
    expected = "John is great"
    mock_sub.return_value = expected
    replace_narrator._narrator_name = "John"
    assert replace_narrator._replace_str("the main character is great") == expected
    mock_sub.assert_called_once()
    assert replace_narrator._replace_str("The PROTAGONIST is great") == expected

@patch.object(ReplaceNarrator, "_replace_str")
@patch.object(ReplaceNarrator, "_handle_value")
def test_replace_narrator_clean_dict(mock_handle_value,mock_replace_str, replace_narrator):
    # sourcery skip: remove-duplicate-dict-key
    mock_handle_value.side_effect = ["value1", "value2", "John","value4"]
    mock_replace_str.side_effect = ["John", "key2", "key3", "key4"]
    value = {"narrator": "value1", "key2": "value2", "key3": "protagonist", "key4": "value"}
    expected = {"John": "value1", "key2": "value2", "key3": "John", "key4": "value4"}
    assert replace_narrator._clean_dict(value) == expected
    assert mock_replace_str.call_count == 4

@patch.object(ReplaceNarrator, "_replace_str")
def test_replace_narrator_clean_list(mock_replace_str, replace_narrator):
    value = ["narrator", "item2", "protagonist", "item4"]
    expected = ["John", "item2", "John", "item4"]
    mock_replace_str.side_effect = expected
    assert replace_narrator._clean_list(value) == expected
    assert mock_replace_str.call_count == 4

@pytest.mark.parametrize(
    ("value", "expected", "mock_dict_call_count", "mock_list_call_count", "mock_str_call_count"),
    [
        (
            {"narrator": "value1", "key2": "value2", "key3": "protagonist", "key4": "value4"},
            {"John": "value1", "key2": "value2", "key3": "John", "key4": "value4"},
            1, 0, 0
        ), # 0
        (
            ["narrator", "item2", "protagonist", "item4"],
            ["John", "item2", "John", "item4"],
            0, 1, 0
        ), # 1
        ("narrator", "John", 0, 0, 1), #2
        (42, 42, 0, 0, 0), #3
        (3.14, 3.14, 0, 0, 0), #4
        (True, True, 0, 0, 0), #5
        (None, None, 0, 0, 0), #6
        ("", "", 0, 0, 1), #7
        (
            ("narrator", "item2", "protagonist", "item4"),
            ("narrator", "item2", "protagonist", "item4"),
            0, 0, 0
        ), #8
    ]
)
@patch.object(ReplaceNarrator, "_replace_str")
@patch.object(ReplaceNarrator, "_clean_list")
@patch.object(ReplaceNarrator, "_clean_dict")
def test_replace_narrator_handle_value(mock_clean_dict, mock_clean_list, mock_replace_str, value, expected, mock_dict_call_count, mock_list_call_count, mock_str_call_count, replace_narrator):
    mock_clean_dict.return_value = expected
    mock_clean_list.return_value = expected
    mock_replace_str.return_value = expected

    replace_narrator._handle_value(value)

    assert mock_clean_dict.call_count == mock_dict_call_count
    assert mock_clean_list.call_count == mock_list_call_count
    assert mock_replace_str.call_count == mock_str_call_count

@patch.object(ReplaceNarrator, "_clean_dict")
def test_replace_narrator_replace(mock_clean_dict, replace_narrator):
    expected = {"John": "value"}
    mock_clean_dict.return_value = expected

    result = replace_narrator.replace("John")

    assert replace_narrator._narrator_name == "John"
    assert result == expected
    mock_clean_dict.assert_called_once()

@patch("lorebinders.data_cleaner.reshape_dict")
@patch("lorebinders.data_cleaner.clean_none_found")
@patch("lorebinders.data_cleaner.DeduplicateKeys")
@patch("lorebinders.data_cleaner.ReplaceNarrator")
@patch("lorebinders.data_cleaner.sort_dictionary") 
def test_clean_lorebinders_all_mocked_called(mock_sort, MockReplace, MockDeduplicate, mock_clean, mock_reshape):
    mock_reshape.return_value = {"test": "value1"}
    mock_clean.return_value = {"test": "value2"}
    mock_deduplicate_method = Mock(return_value={"test": "value3"})
    MockDeduplicate.return_value.deduplicate = mock_deduplicate_method
    mock_replace_method = Mock(return_value={"test": "value4"})
    MockReplace.return_value.replace = mock_replace_method
    mock_sort.return_value = {"test": "value5"}
    lorebinder = {"test": "value"}
    narrator = "John Doe"

    result = clean_lorebinders(lorebinder, narrator)

    assert result == {"test": "value5"}
    mock_reshape.assert_called_once()
    mock_clean.assert_called_once_with({"test": "value1"})
    MockDeduplicate.assert_called_once()
    mock_deduplicate_method.assert_called_once_with({"test": "value2"})
    MockReplace.assert_called_once_with({"test": "value3"})
    mock_replace_method.assert_called_once_with(narrator)
    mock_sort.assert_called_once_with({"test": "value4"})