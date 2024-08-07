import pytest

from lorebinders.data_cleaner import (
    RemoveNoneFound,
    ReplaceNarrator,
    ReshapeDict,
    DeduplicateKeys,
    ManipulateData,
    FinalReshape,
    SortDictionary,
    clean_lorebinders,
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


def test_remove_titles(sample_lorebinder):
    manipulator = ManipulateData()
    assert manipulator.remove_titles("The Narrator") == "Narrator"
    assert manipulator.remove_titles("Narrator") == "Narrator"


def test_to_singular(sample_lorebinder):
    manipulator = ManipulateData()
    assert manipulator.to_singular("Characters") == "Character"
    assert manipulator.to_singular("Actions") == "Action"
    assert manipulator.to_singular("Thoughts") == "Thought"


def test_remove_none_found(sample_lorebinder):
    remove_none = RemoveNoneFound(sample_lorebinder)
    cleaned = remove_none.clean_none_found()
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
