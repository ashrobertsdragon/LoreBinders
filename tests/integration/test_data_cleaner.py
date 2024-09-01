import pytest

from lorebinders.data_cleaner import (
    remove_titles, to_singular, clean_list, clean_none_found, ReplaceNarrator, reshape_dict, final_reshape, DeduplicateKeys, sort_dictionary, clean_lorebinders
)


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
                    "Location": "Suburban",
                },
            },
        },
    }

@pytest.fixture
def deduplicator():
    return DeduplicateKeys()



@pytest.fixture
def replace_narrator(sample_lorebinder):
    return ReplaceNarrator(sample_lorebinder)

def test_remove_none_found():
    cleaned = clean_none_found(sample_lorebinder)
    assert "None found" not in str(cleaned)


def test_deduplicate_keys(sample_lorebinder):
    deduplicator = DeduplicateKeys(sample_lorebinder)
    deduplicated = deduplicator.deduplicated
    assert "Characters" in deduplicated
    assert "Narrator" in deduplicated["Characters"]
    assert "Main Character" in deduplicated["Characters"]


def test_reshape_dict(sample_lorebinder):

    reshaped = reshape_dict(sample_lorebinder)
    assert "Characters" in reshaped
    assert "Narrator" in reshaped["Characters"]
    assert "Thoughts" in reshaped["Characters"]["Narrator"]
    assert "1" in reshaped["Characters"]["Narrator"]["Thoughts"]
    assert "2" in reshaped["Characters"]["Narrator"]["Thoughts"]


def test_final_reshape(sample_lorebinder):
    final_reshaped = final_reshape(sample_lorebinder)
    assert "Characters" in final_reshaped
    assert "Narrator" in final_reshaped["Characters"]
    assert "Thoughts" in final_reshaped["Characters"]["Narrator"]
    assert "1" in final_reshaped["Characters"]["Narrator"]["Thoughts"]
    assert "2" in final_reshaped["Characters"]["Narrator"]["Thoughts"]


def test_sort_dictionary(sample_lorebinder):

    sorted_lorebinder = sort_dictionary(sample_lorebinder)
    assert "Characters" in sorted_lorebinder
    assert "Narrator" in sorted_lorebinder["Characters"]
    assert "1" in sorted_lorebinder["Characters"]["Narrator"]["Thoughts"]
    assert "2" in sorted_lorebinder["Characters"]["Narrator"]["Thoughts"]


def test_replace_narrator(sample_lorebinder):
    replace_narrator = ReplaceNarrator(sample_lorebinder)
    narrator_replaced = replace_narrator.replace("John Doe")
    assert "John Doe" in narrator_replaced["Characters"]
    assert "John Doe" in narrator_replaced["Characters"]["John Doe"]["Actions"]


def test_clean_lorebinders(sample_lorebinder):
    cleaned_lorebinder = clean_lorebinders(sample_lorebinder, "John Doe")
    assert "Characters" in cleaned_lorebinder
    assert "John Doe" in cleaned_lorebinder["Characters"]
    assert "Thoughts" in cleaned_lorebinder["Characters"]["John Doe"]
    assert "1" in cleaned_lorebinder["Characters"]["John Doe"]["Thoughts"]
    assert "2" in cleaned_lorebinder["Characters"]["John Doe"]["Thoughts"]

# Tests for clean_list function
def test_clean_list_strings_remove_none_found():
    test_list = ["test1", "none found"]
    assert clean_list(test_list) == ["test1"]

def test_clean_list_strings_no_changes():
    test_list = ["test1", "test2"]
    assert clean_list(test_list) == test_list

def test_clean_list_dict_remove_none_found():
    test_list = [{"test": "none found"}]
    assert clean_list(test_list) == []

def test_clean_list_dict_no_changes():
    test_list = [{"test": "value"}]
    assert clean_list(test_list) == test_list

def test_clean_list_nested_list_remove_none_found():
    test_list = ["test", ["none found"]]
    assert clean_list(test_list) == ["test"]

def test_clean_list_nested_list_no_changes():
    test_list = ["test", ["nested"]]
    assert clean_list(test_list) == ["test", ["nested"]]

def test_clean_list_mixed_types_remove_none_found():
    test_list = ["test", ["nested", "none found"], {"key": "value"}]
    assert clean_list(test_list) == ["test", ["nested"], {"key": "value"}]

def test_clean_list_mixed_types_no_changes():
    test_list = ["test", ["nested"], {"key": "value"}]
    assert clean_list(test_list) == test_list

# Tests for clean_none_found function
def test_clean_none_found_clean_string_values():
    test_dict = {"key1": "value", "key2": "none found"}
    assert clean_none_found(test_dict) == {"key1": "value"}

def test_clean_none_found_clean_string_values_no_changes():
    test_dict = {"key1": "value1", "key2": "value2"}
    assert clean_none_found(test_dict) == test_dict

def test_clean_none_found_clean_list_no_items():
    test_dict = {"key": ["none found"]}
    assert clean_none_found(test_dict) == {}

def test_clean_none_found_clean_list_one_item():
    test_dict = {"key": ["value1", "none found"]}
    assert clean_none_found(test_dict) == {"key": "value1"}

def test_clean_none_found_clean_list_two_items():
    test_dict = {"key": ["value1", "value2"]}
    assert clean_none_found(test_dict) == test_dict

def test_clean_none_found_mixed_types_remove_none_found():
    test_dict = {"key": ["value1", "value2", "none found"], "key2": "value3", "key3": {"key4": "value4"}, "key5": "none found", "key6": {"key7": "none found"}, "key8": ["none found"], "key9": ["none found", "value5"]}
    assert clean_none_found(test_dict) == {"key": ["value1", "value2"], "key2": "value3", "key3": {"key4": "value4"}, "key9": "value5"}

def test_clean_none_found_mixed_types_no_changes():
    test_dict = {"key": ["value1", "value2"], "key2": "value3", "key3": {"key4": "value4"}}
    assert clean_none_found(test_dict) == test_dict

# test DeduplicateKeys
def test_deduplicate_keys_deduplicate_similar_keys(deduplicator):
    binder = {"outer": {"key1": "value1", "key2": "value2"}}
    expected_result = {"outer": {"key2": ["value1", "value2"]}}

    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result

def test_deduplicate_keys_deduplicate_non_similar_keys(deduplicator):
    binder = {"outer": {"inner1": "value1", "key2": "value2"}}
    expected_result = binder  # No changes expected

    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result

def test_deduplicate_keys_deduplicate_no_inner(deduplicator):
    binder = {"outer1": {"key1": "value1"}, "outer2": {"key2": "value2"}}
    expected_result = binder  # No changes expected
    
    result = deduplicator.deduplicate(binder)
    
    assert result == expected_result


@pytest.mark.parametrize(
    ("key1", "key2", "expected"),
    [
        ("short", "longer", ("short", "longer")),
        ("longer", "short", ("short", "longer")),
        ("King", "King Edward", ("King Edward", "King")),
        ("King Edward", "King", ("King Edward", "King")),
        ("Short", "longer", ("Short", "longer")),
        ("short", "Longer", ("short", "Longer")),
        ("", "test", ("", "test")),
        ("test", "", ("", "test")),
        ("", "King Edward", ("", "King Edward")),
        ("King Edward", "", ("", "King Edward")),
        ("", "", ("", "")),
        ("test", "test", ("test", "test")),
        ("test1", "test2", ("test1", "test2")),
        ("king", "queen", ("king", "queen")),
    ]
)
def test_deduplicate_keys_prioritize_keys(mock_is_title, key1, key2, expected, deduplicator):
    result = deduplicator._prioritize_keys(key1, key2)
    assert result == expected

@pytest.mark.parametrize(
    ("key1", "key2", "expected"),
    [
        ("cat", "cats", True),
        ("cats", "cat", True),
        ("cats", "cats", True),
        (" cat", "cat", True),
        ("cat ", "cat", True),
        (" cat ", "cat", True),
        ("cat", " cat", True),
        ("cat", "cat ", True),
        ("cat", " cat ", True),
        ("cat", "dog", False),
        ("cat", "CAT", True),
        ("Mr. Smith", "Smith", True),
        ("Smith", "Mr. Smith", True),
        ("Mr. Smith", "Mr. Smith", True),
        ("Mr. Smith", "Smiths", True),
        ("Smiths", "Mr. Smith", True),
        ("Mr. Smith", "Mr. Smiths", True),
        ("Mr. Smiths", "Mr. Smith", True),
        ("Mr. Smiths", "Mr. Smiths", True),
        ("Mr. Smiths", "Smith", False),
        ("King", "King Edward", True),
        ("King Edward", "King", True),
        ("KiNg", "kInG eDwArD", True),
        ("KiNg eDwArD", "kInG", True),
        ("Queen", "King Edward", False),
        ("King Edward", "Queen", False),
        ("Red Dragon", "Dragon", False),
        ("Dragon", "Red Dragon", False),
        ("dogs", "cats", False),
        ("cats", "dogs", False),
        ("Mr. Smith", "Smith Hall", True),
        ("Smith Hall", "Mr. Smith", True),
        ("Mr. Smith", "blacksmith", False),
        ("blacksmith", "Mr. Smith", False),
        ("King", "Kingdom", False),
        ("Kingdom", "King", False)
    ]
)
def test_deduplicate_keys_is_similar(key1, key2,  expected, deduplicator):
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
def test_deduplicate_keys_is_title(case, expected, deduplicator):
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
            }
        ), # case 0
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
            }
        ), # case 1
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter1": {"Details": "New Details"}}}},
            {"Characters": {"Name1": {"Chapter1": {"Details": ["Existing Details", "New Details"]}}}}
        ),# case 2
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter2": {"Details": "New Chapter Details"}}}},
            {
                "Characters": {
                    "Name1": {
                        "Chapter1": {"Details": "Existing Details"},
                        "Chapter2": {"Details": "New Chapter Details"}
                    }
                }
            } 
        ), # case 3
        (
            {"Characters": {"Name1": {"Chapter1": {"Details": "Existing Details"}}}, "Category1": {"Name1": {"Chapter2": "Non-dict Details"}}},
            {"Characters": {
                "Name1": {"Chapter1": {"Details": "Existing Details"}, "Chapter2": {"Also": "Non-dict Details"}}}}
        ) # case 4
    ]
)
def test_deduplicate_across_dictionaries(summaries, expected_result, deduplicator):
    result = deduplicator._deduplicate_across_dictionaries(summaries)
    assert result == expected_result

def test_deduplicate_across_dictionaries_keys_deleted(deduplicator):
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


def test_deduplicate_keys_merge_values_merge_two_dicts(deduplicator):
    result = deduplicator._merge_values({"key1": "value1"}, {"key2": "value2"})
    assert result == {"key1": "value1", "key2": "value2"}

def test_deduplicate_keys_merge_values_merge_two_lists(deduplicator):
    result = deduplicator._merge_values([1, 2], [3, 4])
    assert result == [1, 2, 3, 4]

def test_deduplicate_keys_merge_values_merge_list_and_dict_no_overlap(deduplicator):
    result = deduplicator._merge_values([{"a": 1}, "test"], {"b": 2, "c": 3})
    assert result == [{"a": 1, "b": 2, "c": 3}, "test"]

def test_deduplicate_keys_merge_values_merge_list_and_dic_overlap(deduplicator):
    result = deduplicator._merge_values([{"a": 1}, "test"], {"a": 1, "b": 2, "c": 3})
    assert result == [{"a": 1, "b": 2, "c": 3}, "test"]

def test_deduplicate_keys_merge_values_invalid_type_with_dict(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, {"key": "value"})

def test_deduplicate_keys_merge_values_invalid_type_with_list(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, [1, 2])

def test_deduplicate_keys_merge_values_invalid_type_with_string(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, "string_value")

def test_deduplicate_keys_merge_values_dict_with_invalid_type(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, {"key": "value"})

def test_deduplicate_keys_merge_values_list_with_invalid_type(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, [1, 2])

def test_deduplicate_keys_merge_values_string_with_invalid_type(deduplicator):
    with pytest.raises(TypeError):
        deduplicator._merge_values(123, "string_value")

def test_deduplicate_keys_merge_dictionary_and_list(deduplicator):
    dict_value = {"key1": "value1"}
    list_value = ["item1", "item2"]
    result = deduplicator._merge_values(dict_value, list_value)
    assert result == {"key1": "value1", "Also": ["item1", "item2"]}

def test_deduplicate_keys_merge_values_recursive(deduplicator):
    dict_value = {"Also": "value1"}
    list_value = ["item1", "item2"]
    result = deduplicator._merge_values(dict_value, list_value)
    assert result == {"Also": ["item1", "item2", "value1"]}

@pytest.mark.parametrize(("value", "expected_result"),
    [("He is narrator.", "He is John Doe."),
     ("He is protagonist.", "He is John Doe."),
     ("He is the main character.", "He is John Doe."),
     ("He is main character.", "He is John Doe.")
     ]
)
def test_replace_narrator_replace_str(value, expected_result, replace_narrator):
    replace_narrator._narrator_name = "John Doe"
    assert replace_narrator._replace_str(value) == expected_result

def test_replace_narrator_clean_dict(replace_narrator):
    # sourcery skip: remove-duplicate-dict-key
    value = {"narrator": "value1", "key2": "value2", "protagonist": "value3", "key4": "value"}
    expected = {"John": "value1", "key2": "value2", "John": "value3", "key4": "value"}
    replace_narrator._narrator_name = "John"
    assert replace_narrator._clean_dict(value) == expected

def test_replace_narrator_clean_list(replace_narrator):
    value = ["narrator", "item2", "protagonist", "item4"]
    expected = ["John", "item2", "John", "item4"]
    replace_narrator._narrator_name = "John"
    assert replace_narrator._clean_list(value) == expected

@pytest.mark.parametrize(
    ("value", "expected", "valid"),
    [
        ({"key1": "John", "key2": "value2", "protagonist": "value3", "key4": "value"}, {"key1": "John", "key2": "value2", "John": "value3", "key4": "value"}),
        (["narrator", "item2", "protagonist", "item4"], ["John", "item2", "John", "item4"]),
        ("narrator", "John"),
        (42, 42),
        (3.14, 3.14),
        (True, True),
        (None, None),
        ("", ""),
        ([], []),
        ({}, {}),
        (("narrator", "item2", "protagonist", "item4"), ("narrator", "item2", "protagonist", "item4")),
    ]
)
def test_replace_narrator_handle_value(value, expected, replace_narrator):
    replace_narrator._narrator_name = "John"
    assert replace_narrator._handle_value(value) == expected
    assert type(value) == type(expected)

@pytest.mark.parametrize(
    ("value", "expected", "valid"),
    [
        (42, 42),
        (3.14, 3.14),
        (True, True),
        (None, None),
        (("narrator", "item2", "protagonist", "item4"), ("narrator", "item2", "protagonist", "item4")),
    ]
)
def test_replace_narrator_handle_value_does_not_modify_invalid_type(value, expected, replace_narrator):
    replace_narrator._narrator_name = "John"
    assert replace_narrator._handle_value(value) == expected
    assert type(value) == type(expected)
    assert value is expected

def test_replace_narrator_replace(replace_narrator):
    # sourcery skip: remove-duplicate-dict-key
    result = replace_narrator.replace("John")
    assert replace_narrator._narrator_name == "John"
    assert result == {
        "1": {
            "Characters": {
                "John": {
                    "Thoughts": "I wonder what will happen.",
                    "Actions": "John walks to the store.",
                },
                "John": {
                    "Thoughts": "I am John.",
                    "Actions": "John goes home.",
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
                    "Actions": "John goes to the park.",
                },
                "John": {
                    "Thoughts": "I am John.",
                    "Actions": "John talks to John.",
                },
            },
            "Settings": {
                "The Park": {
                    "Description": "It is a large park.",
                    "Location": "Suburban",
                },
            },
        },
    }