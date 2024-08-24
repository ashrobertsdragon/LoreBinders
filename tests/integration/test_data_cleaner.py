import pytest

from lorebinders.data_cleaner import (
    remove_titles, to_singular, clean_list, clean_none_found, ReplaceNarrator, ReshapeDict, FinalReshape, DeduplicateKeys, SortDictionary, clean_lorebinders
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
    reshaper = ReshapeDict(sample_lorebinder)
    reshaped = reshaper.reshaped
    assert "Characters" in reshaped
    assert "Narrator" in reshaped["Characters"]
    assert "Thoughts" in reshaped["Characters"]["Narrator"]
    assert "1" in reshaped["Characters"]["Narrator"]["Thoughts"]
    assert "2" in reshaped["Characters"]["Narrator"]["Thoughts"]


def test_final_reshape(sample_lorebinder):
    final_reshaper = FinalReshape(sample_lorebinder)
    final_reshaped = final_reshaper.reshaped
    assert "Characters" in final_reshaped
    assert "Narrator" in final_reshaped["Characters"]
    assert "Thoughts" in final_reshaped["Characters"]["Narrator"]
    assert "1" in final_reshaped["Characters"]["Narrator"]["Thoughts"]
    assert "2" in final_reshaped["Characters"]["Narrator"]["Thoughts"]


def test_sort_dictionary(sample_lorebinder):
    sorter = SortDictionary(sample_lorebinder)
    sorted_lorebinder = sorter.sorted_dict
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
