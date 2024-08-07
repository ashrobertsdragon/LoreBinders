from collections import defaultdict

import pytest

from lorebinders.sort_names import SortNames


@pytest.fixture
def sort_names():
    name_list = """
    Characters:
    Esgeril
    Colonel Authand
    Pene
    Florian
    Cadi
    Farean,
    Federa
    Lewon
    Calen
    Narrator
    Settings:
    Cafeteria (interior)
    Field (exterior)
    Trees (exterior)
    Stream (exterior)
    """
    narrator = "Kalia"
    return SortNames(name_list, narrator)


def test_sort_names(sort_names):
    expected_dict = {
        "Characters": [
            "Esgeril",
            "Colonel Authand",
            "Pene",
            "Florian",
            "Cadi",
            "Farean",
            "Federa",
            "Lewon",
            "Calen",
            "Kalia",
        ],
        "Settings": [
            "Cafeteria (interior)",
            "Field (exterior)",
            "Trees (exterior)",
            "Stream (exterior)",
        ],
    }
    ner_dict = sort_names.sort()
    assert ner_dict == expected_dict


def test_compare_names(sort_names):
    inner_values = ["John", "Jon", "Jonathan", "Johnny"]
    name_map = {}
    result = sort_names._compare_names(inner_values, name_map)
    assert "Jon" in result
    assert "Jonathan" in result


def test_get_shorter_longer(sort_names):
    shorter, longer = sort_names._sort_shorter_longer("Jon", "Jonathan")
    assert shorter == "Jon"
    assert longer == "Jonathan"


def test_has_narrator(sort_names):
    narrators = ["narrator", "protagonist", "main character"]
    for narrator in narrators:
        assert sort_names._has_narrator(narrator)
    assert not sort_names._has_narrator("some other text")


def test_ends_with_colon(sort_names):
    assert sort_names._ends_with_colon("Characters:")
    assert not sort_names._ends_with_colon("Esgeril")


def test_lowercase_interior_exterior(sort_names):
    result = sort_names._lowercase_interior_exterior("INTERIOR room")
    assert result == "interior room"


def test_remove_leading_colon_pattern(sort_names):
    result = sort_names._remove_leading_colon_pattern(": leading colon")
    assert result == "leading colon"


def test_remove_list_formatting(sort_names):
    result = sort_names._remove_list_formatting("1. list item")
    assert result == "list item"


def test_remove_parentheses(sort_names):
    result = sort_names._remove_parentheses("(parentheses)")
    assert result == "parentheses"


def test_replace_bad_setting(sort_names):
    result = sort_names._replace_bad_setting("Setting:")
    assert result == "Settings:"


def test_replace_inverted_setting(sort_names):
    result = sort_names._replace_inverted_setting("interior (room)")
    assert result == "room (interior)"


def test_split_settings_line(sort_names):
    line = "interior: room, house"
    expected_split_lines = ["room (interior)", "house (interior)"]
    split_lines, added_lines = sort_names._split_settings_line(line)
    assert split_lines == expected_split_lines
    assert added_lines == 1


def test_split_at_commas(sort_names):
    line = "name1, name2, name3"
    expected_split_lines = ["name1", "name2", "name3"]
    split_lines, added_lines = sort_names._split_at_commas(line)
    assert split_lines == expected_split_lines
    assert added_lines == 2


def test_replace_narrator(sort_names):
    sort_names._lines = ["main character"]
    sort_names._narrator = "John Doe"
    sort_names.sort()
    assert sort_names._lines[0] == "John Doe"


def test_sort_names_invalid_state_empty_lines(sort_names):
    sort_names._lines = []
    expected_dict = defaultdict(str)
    ner_dict = sort_names.sort()
    assert ner_dict == expected_dict


def test_sort_names_invalid_state_empty_string(sort_names):
    sort_names._lines = [""]
    expected_dict = defaultdict(str)
    ner_dict = sort_names.sort()
    assert ner_dict == expected_dict


def test_sort_shorter_longer(sort_names):
    assert sort_names._sort_shorter_longer("Pene", "Pene's") == (
        "Pene",
        "Pene's",
    )
    assert sort_names._sort_shorter_longer("Pene's", "Pene.") == (
        "Pene",
        "Pene's.",
    )


def test_should_compare_values(sort_names):
    assert sort_names._should_compare_values("Pene", "Pene's")
    assert not sort_names._should_compare_values("Pene", "Florian")
    assert not sort_names._should_compare_values("Lake (exterior)", "Lake")
    assert not sort_names._should_compare_values("Lake", "Lake (exterior)")


def test_should_skip_line(sort_names):
    assert sort_names._should_skip_line("he")
    assert not sort_names._should_skip_line("Pene")


def test_has_odd_parentheses(sort_names):
    assert sort_names._has_odd_parentheses("(interior")
    assert not sort_names._has_odd_parentheses("(interior)")


def test_is_list_as_str(sort_names):
    assert sort_names._is_list_as_str("Pene, Florian, Cadi")
    assert not sort_names._is_list_as_str("Pene")


def test_starts_with_location(sort_names):
    assert sort_names._starts_with_location("interior:")
    assert not sort_names._starts_with_location("Cafeteria (interior)")
