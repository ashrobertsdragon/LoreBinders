from calendar import c
from unittest.mock import call, patch, Mock

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
    with patch('lorebinders.sort_names.defaultdict') as mock_defaultdict:
        mock_defaultdict.return_value = {}
        return SortNames(name_list, narrator)

@patch.object(SortNames, "_set_regex_patterns")
def test_sort_names_init_with_narrator(mock_set_regex_patterns):
    name_list = "Characters:\nAlice\nBob\nSettings:\nForest (exterior)"
    narrator = "Alice"

    sort_names = SortNames(name_list, narrator)

    assert sort_names._lines == ["Characters:", "Alice", "Bob", "Settings:", "Forest (exterior)"]
    assert sort_names._narrator == "Alice"
    assert sort_names.ner_dict == {}
    assert sort_names._category_dict == {}
    assert sort_names._category_name == ""
    assert sort_names._inner_values == []
    mock_set_regex_patterns.assert_called_once()
    assert sort_names._junk_words == {
            "additional",
            "note",
            "none",
            "mentioned",
            "unknown",
            "he",
            "they",
            "she",
            "we",
            "it",
            "boy",
            "girl",
            "main",
            "him",
            "her",
            "I",
            "</s>",
            "a",
        }


@patch("lorebinders.sort_names.defaultdict")
def test_sort_names_init_with_empty_narrator( mock_defaultdict):
    mock_defaultdict.return_value = {}
    name_list = "Characters:\nAlice\nBob\nSettings:\nForest (exterior)"
    sort_names = SortNames(name_list, "")
    assert sort_names._narrator == ""

@patch("lorebinders.sort_names.defaultdict")
def test_sort_names_init_with_no_narrator( mock_defaultdict):
    mock_defaultdict.return_value = {}
    name_list = "Characters:\nAlice\nBob\nSettings:\nForest (exterior)"
    sort_names = SortNames(name_list)
    assert sort_names._narrator == ""

@patch("lorebinders.sort_names.defaultdict")
def test_sort_names_init_with_None_narrator( mock_defaultdict):
    mock_defaultdict.return_value = {}
    name_list = "Characters:\nAlice\nBob\nSettings:\nForest (exterior)"
    sort_names = SortNames(name_list, None)
    assert sort_names._narrator == ""

@patch.object(SortNames, "_set_regex_patterns")
def test_sort_names_init_without_narrator(mock_set_regex_patterns):
    name_list = "Characters:\nAlice\nBob\nSettings:\nForest (exterior)"

    sort_names = SortNames(name_list)

    assert sort_names._narrator == ""
    mock_set_regex_patterns.assert_called_once()

@patch("lorebinders.sort_names.re.compile")
def test_sort_names_set_regex_patterns(mock_re_compile):
    mock_re_compile.side_effect = [
        r"\((?!interior|exterior).+\)$",
        r"(interior|exterior)\s+\((\w+)\)",
        r"\s*:\s+",
        r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t",
        r"(?<=\w)(?=[A-Z][a-z]*:)",
        r"(\w+ \(\w+\))\s+(\w+)",
        r"(?<=\w):\s*(?=\w)",
    ]
    sort_names = SortNames("")
    assert mock_re_compile.call_count == 7
    assert sort_names._not_int_ext_parenthetical_pattern == r"\((?!interior|exterior).+\)$"
    assert sort_names._inverted_setting_pattern == r"(interior|exterior)\s+\((\w+)\)"
    assert sort_names._leading_colon_pattern == r"\s*:\s+"
    assert sort_names._list_formatting_pattern == r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t"
    assert sort_names._missing_newline_before_pattern == r"(?<=\w)(?=[A-Z][a-z]*:)"
    assert sort_names._missing_newline_between_pattern == r"(\w+ \(\w+\))\s+(\w+)"
    assert sort_names._missing_newline_after_pattern == r"(?<=\w):\s*(?=\w)"

@patch("re.sub")
def test_sort_names_lowercase_interior_exterior_converts_INTERIOR_to_interior(mock_sub, sort_names):
    mock_sub.return_value = "interior"
    result = sort_names._lowercase_interior_exterior("INTERIOR")
    assert result == "interior"
    mock_sub.assert_called_once()

@patch("re.sub")
def test_sort_names_lowercase_interior_exterior_converts_EXTERIOR_to_exterior(mock_sub, sort_names):
    mock_sub.return_value = "exterior"
    result = sort_names._lowercase_interior_exterior("EXTERIOR")
    assert result == "exterior"
    mock_sub.assert_called_once()

def test_sort_names_remove_list_formatting(sort_names):
    with patch.object(sort_names, "_list_formatting_pattern") as mock_list_formatting_pattern:
        mock_list_formatting_pattern.sub.return_value = "test"

        result = sort_names._remove_list_formatting("1. test")

        assert result == "test"
        mock_list_formatting_pattern.sub.assert_called_once()

def test_sort_names_remove_parentheses(sort_names):
    line = "test (test)"

    result = sort_names._remove_parentheses(line)

    assert result == "test test"

def test_sort_names_remove_parentheses_no_parentheses(sort_names):
    line = "test"

    result = sort_names._remove_parentheses(line)

    assert result == "test"

def test_sort_names_replace_bad_setting(sort_names):
    result = sort_names._replace_bad_setting()
    assert result == "Settings:"

def test_sort_names_replace_inverted_setting(sort_names):
    with patch.object(sort_names, "_inverted_setting_pattern") as mock_inverted_setting_pattern:
        mock_inverted_setting_pattern.sub.return_value = "Cafeteria (interior)"
        line = "interior (Cafeteria)"

        result = sort_names._replace_inverted_setting(line)

        assert result == "Cafeteria (interior)"
        mock_inverted_setting_pattern.sub.assert_called_once()

def test_sort_names_num_added_lines(sort_names):
    # 1 subtracted because originally single line and measuring how many lines were extended by
    split_lines =["test","test","test"]

    result = sort_names._num_added_lines(split_lines)

    assert result == 2


@patch.object(SortNames, "_missing_newline_patterns")
def test_sort_names_needs_newline_returns_true_if_modified(mock_patterns, sort_names):
    mock_patterns.return_value = ["modified_line", "original_line"]
    result = sort_names._needs_newline("original_line")
    assert result

@patch.object(SortNames, "_missing_newline_patterns")
def test_sort_names_needs_newline_returns_false_if_not_modified(mock_patterns, sort_names):
    mock_patterns.return_value = ["original_line", "original_line"]
    result = sort_names._needs_newline("original_line")
    assert not result

@patch.object(SortNames, "_missing_newline_patterns")
def test_sort_names_add_missing_newline(mock_missing_newline_patterns, sort_names):
    mock_missing_newline_patterns.return_value = ["test test", "test\ntest", "test test"]

    result = sort_names._add_missing_newline("test test")
    assert result == (["test", "test"], 1)

@patch.object(SortNames, "_num_added_lines")
def test_sort_names_split_at_commas(mock_num_added_lines, sort_names):
    mock_num_added_lines.return_value = 2
    line = "test, test, test"
    expected_result = ["test", "test", "test"]

    result = sort_names._split_at_commas(line)

    assert result == (expected_result, 2)
    mock_num_added_lines.assert_called_once_with(expected_result)

@patch.object(SortNames, "_num_added_lines")
def test_sort_names_split_settings_line(mock_num_added_lines, sort_names):
    mock_num_added_lines.return_value = 2
    line = "interior: test, test, test"
    expected_result = ["test (interior)", "test (interior)", "test (interior)"]

    result = sort_names._split_settings_line(line)

    assert result == (expected_result, 2)
    mock_num_added_lines.assert_called_once_with(expected_result)

def test_sort_names_ends_with_colon(sort_names):
    line1 = "test:"
    line2 = "test"
    line3 = "test: "


    result1 = sort_names._ends_with_colon(line1)
    result2 = sort_names._ends_with_colon(line2)
    result3 = sort_names._ends_with_colon(line3)

    assert result1
    assert not result2
    assert not result3

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("setting:", True),
        ("location:", True),
        ("locations:", True),
        ("places:", True),
        ("place:", True),
        ("settings:", False),
        ("Settings:", False),
        ("Setting:", True),
        ("Location:", True),
        ("Locations:", True),
        ("Places:", True),
        ("Place:", True)
    ],
)
def test_sort_names_has_bed_setting(line, expected, sort_names):

    result = sort_names._has_bad_setting(line)

    assert result == expected

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Narrator", True),
        ("narrator", True),
        ("protagonist", True),
        ("main character", True),
        ("Protagonist", True),
        ("Main Character", True),
        ("Kalia", False),
        ("test", False),
        ("The narrator is Kalia", True),
        ("The Narrator is Kalia", True),
        ("The protagonist is Kalia", True),
        ("The Protagonist is Kalia", True),
        ("The main character is Kalia", True),
        ("The Main Character is Kalia", True)
    ],
)
def test_sort_names_has_narrator(line, expected, sort_names):
    result = sort_names._has_narrator(line)
    assert sort_names._narrator == "Kalia"
    assert result == expected

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("test (test)", False),
        ("test (test", True),
        ("test test)", True),
        ("test test", False),
        ("(())", False),
        ("(test (test)", True),
        ("test (test))", True)
    ],
)
def test_sort_names_has_odd_parentheses(line, expected, sort_names):

    result = sort_names._has_odd_parentheses(line)

    assert result == expected

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("test, test, test", True),
        ("test test", False),
        ("test test, test", True),
        ("test test, test test", True)
    ],
)
def test_sort_names_is_list_as_str(line, expected,sort_names):
    result = sort_names._is_list_as_str(line)

    assert result == expected

@pytest.mark.parametrize(
    ("value_i", "value_j", "expected"),
    [
        ("test", "test", False),
        ("test)", "test", False),
        ("test", "test)", False),
        ("test1", "test", True),
        ("test", "test1", False),
        ("1test", "test", True),
        ("test", "1test", False),
        ("a_test1", "test", False),
        ("test", "a_test1", False),
        ("Alice", "Bob", False),
        ("Bobby", "Bob", True)
    ],
)
def test_sort_names_should_compare_values(value_i, value_j, expected, sort_names):
    result = sort_names._should_compare_values(value_i, value_j)
    assert result == expected

def test_sort_names_should_skip_line_true_lower(sort_names):
    with patch.object(sort_names, '_junk_words', {"alpha", "beta", "gamma"}):
        line = "test alpha"
        result = sort_names._should_skip_line(line)
        assert result


def test_sort_names_should_skip_line_true_upper(sort_names):
    with patch.object(sort_names, '_junk_words', {"alpha", "beta", "gamma"}):
        line = "test Alpha"
        result = sort_names._should_skip_line(line)
        assert result


def test_sort_names_should_skip_line_false(sort_names):
    with patch.object(sort_names, '_junk_words', {"alpha", "beta", "gamma"}):
        line = "test this line"
        result = sort_names._should_skip_line(line)
        assert not result

def test_sort_names_should_skip_line_blank_line(sort_names):
    with patch.object(sort_names, '_junk_words', {"alpha", "beta", "gamma"}):
        line = ""
        result = sort_names._should_skip_line(line)
        assert result

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("test", False),
        ("interior: test", True),
        ("exterior: test", True),
        ("interior test", False),
        ("exterior test", False),
        ("test (interior)", False),
        ("test (exterior)", False),
        ("test exterior", False),
        ("test interior", False),
        ("test: test", False),
        ("(interior) test", False),
        ("(exterior) test", False)
    ]
)
def test_sort_names_starts_with_location(line, expected, sort_names):
    result = sort_names._starts_with_location(line)
    assert result == expected

@patch.object(SortNames, "_ends_with_colon", return_value=True)
@patch.object(SortNames, "_set_category_dict")
def test_sort_names_add_to_dict_add_category(mock_set_category_dict, mock_ends_with_colon, sort_names):
    line = "test:"

    sort_names._add_to_dict(line)

    mock_ends_with_colon.assert_called_once_with(line)
    mock_set_category_dict.assert_not_called()
    assert sort_names._category_name == "Test"

@patch.object(SortNames, '_ends_with_colon', return_value=False)
@patch.object(SortNames, '_set_category_dict')
def test_sort_names_add_to_dict_add_inner_value(mock_set_category_dict, mock_ends_with_colon, sort_names):
    line = "test"

    sort_names._add_to_dict(line)

    mock_ends_with_colon.assert_called_once_with(line)
    mock_set_category_dict.assert_not_called()
    assert sort_names._inner_values == ["test"]

def test_sort_names_set_category_dict_new_dict(sort_names):
    sort_names._inner_values = ["test"]
    sort_names._category_name = "Test Category"

    sort_names._set_category_dict()

    assert sort_names._category_dict == {"Test Category": ["test"]}
    assert not sort_names._inner_values

def test_sort_names_set_category_dict_existing_dict(sort_names):
    sort_names._inner_values = ["test2"]
    sort_names._category_name = "Test Category"
    sort_names._category_dict = {"Test Category": ["test1"]}

    sort_names._set_category_dict()

    assert sort_names._category_dict == {"Test Category": ["test1", "test2"]}
    assert not sort_names._inner_values


def test_combine_singular_to_plural_combines_forms(sort_names):
    sort_names._category_dict = {
        "books": ["book1", "book2"],
        "book": ["book3"]
    }
    result = sort_names._combine_singular_to_plural("books")
    assert result == ["book1", "book2", "book3"]
    assert sort_names._category_dict["book"] == []

def test_sort_names_combine_singular_to_plural_no_singular_form(sort_names):
    sort_names._category_dict = {
        "books": ["book1", "book2"]
    }
    result = sort_names._combine_singular_to_plural("books")
    assert result == ["book1", "book2"]
    assert sort_names._category_dict["books"] == ["book1", "book2"]

@patch.object(SortNames, "_compare_names")
@patch.object(SortNames, "_combine_singular_to_plural")
def test_sort_names_build_ner_dict_unique_categories(mock_combine_singular_to_plural, mock_compare_names, sort_names):
    mock_combine_singular_to_plural.return_value = ["standardized_name1", "standardized_name2"]
    mock_compare_names.return_value = ["standardized_name1", "standardized_name2"]

    sort_names._category_dict = {
        "category1": ["name1", "name2"],
        "category2": ["name3", "name4"]
    }

    result =sort_names._build_ner_dict()

    assert result == {
        "category1": ["standardized_name1", "standardized_name2"],
        "category2": ["standardized_name1", "standardized_name2"]
    }
    assert mock_compare_names.call_count == 2

@patch.object(SortNames, "_compare_names")
@patch.object(SortNames, "_combine_singular_to_plural")
def test_sort_names_build_ner_dict_plural_no_singular(mock_combine_singular_to_plural, mock_compare_names, sort_names):
    mock_compare_names.return_value = ["standardized_name1", "standardized_name2"]

    mock_combine_singular_to_plural.return_value = ["standardized_name1", "standardized_name2"]

    sort_names._category_dict = {
        "categories": ["name1", "name2"],
        "other_category": ["name3", "name4"]
    }

    result = sort_names._build_ner_dict()

    assert result == {
        "categories": ["standardized_name1", "standardized_name2"],
        "other_category": ["standardized_name1", "standardized_name2"]
    }
    assert mock_compare_names.call_count == 2

@patch.object(SortNames, "_compare_names")
@patch.object(SortNames, "_combine_singular_to_plural")
def test_sort_names_build_ner_dict_singular_and_plural_keys(mock_combine_singular_to_plural, mock_compare_names, sort_names):
    mock_combine_singular_to_plural.side_effect = [["apple1, apple2"], ["orange1"], ["banana1"], [], ["pear1"]]
    mock_compare_names.side_effect = [["apple1, apple2"], ["orange1"], ["banana1"], ["pear1"]]
    sort_names._category_dict = {
        "apples": ["apple1"],
        "oranges": ["orange1"],
        "bananas": ["banana1"],
        "apple": ["apple2"],
        "pears": ["pear1"]
    }
    expected_ner_dict = {
        "apples": ["apple1, apple2"],
        "oranges": ["orange1"],
        "bananas": ["banana1"],
        "pears": ["pear1"]
    }

    result =sort_names._build_ner_dict()

    assert result == expected_ner_dict
    assert mock_compare_names.call_count == 4
    mock_compare_names.assert_any_call(["apple1, apple2"])
    mock_compare_names.assert_any_call(["orange1"])
    mock_compare_names.assert_any_call(["banana1"])
    mock_compare_names.assert_any_call(["pear1"])

def test_raises_type_error_if_inner_values_not_list(sort_names):
    with pytest.raises(TypeError):
       sort_names._compare_names(sort_names, inner_values="not_a_list")

@patch("lorebinders.data_cleaner.remove_titles")
@patch.object(SortNames, "_should_compare_values", return_value=True)
@patch.object(SortNames, "_sort_shorter_longer")
def test_sort_names_compare_names_single_set_of_names(mock_sort, mock_compare, mock_remove, sort_names):
    mock_remove.side_effect = ["John", "John Smith"]
    mock_sort.return_value = ("John", "John Smith")
    inner_values = ["Dr. John", "Mr. John Smith"]
    expected = ["John Smith"]

    result = sort_names._compare_names(inner_values)
    assert result == expected

@patch("lorebinders.data_cleaner.remove_titles")
@patch.object(SortNames, "_should_compare_values")
@patch.object(SortNames, "_sort_shorter_longer")
def test_sort_names_compare_names_multiple_item_list(mock_sort, mock_compare, mock_remove, sort_names):
    mock_remove.side_effect = ["John", "John Smith", "Jane Doe", "J. Doe"]
    mock_compare.side_effect = [True, False, False, False, False, True]
    mock_sort.side_effect = [("John", "John Smith"), ("J. Doe", "Jane Doe")]
    inner_values = ["Dr. John", "John Smith", "Ms. Jane Doe", "J. Doe"]
    expected = ["John Smith", "Jane Doe"]

    result = sort_names._compare_names(inner_values)
    assert sorted(result) == sorted(expected)

@patch("lorebinders.data_cleaner.remove_titles")
def test_sort_names_compare_names_empty_list(mock_remove, sort_names):
    inner_values = []
    expected = []
    result = sort_names._compare_names(inner_values)
    assert result == expected

@patch("lorebinders.data_cleaner.remove_titles")
@patch.object(SortNames, "_should_compare_values", return_value=True)
@patch.object(SortNames, "_sort_shorter_longer")
def test_sort_names_compare_names_remove_titles_from_names(mock_sort, mock_compare, mock_remove, sort_names):
    mock_remove.side_effect = ["John", "John Smith"]
    mock_sort.return_value = ("John", "John Smith")
    inner_values = ["Dr. John", "Mr. John Smith"]

    sort_names._compare_names(inner_values)

    mock_remove.assert_any_call("Dr. John")
    mock_remove.assert_any_call("Mr. John Smith")

@patch("lorebinders.data_cleaner.remove_titles")
@patch.object(SortNames, "_should_compare_values")
@patch.object(SortNames, "_sort_shorter_longer")
def test_sort_names_compare_names_apply_name_map_to_each_name(mock_sort, mock_compare, mock_remove, sort_names):
    mock_remove.side_effect = ["John", "John Smith", "Jane"]
    mock_compare.side_effect = [True, False, False]
    mock_sort.return_value = ("John", "John Smith")
    inner_values = ["Dr. John", "Mr. John Smith", "Ms. Jane"]
    expected = ["John Smith", "Jane"]

    result = sort_names._compare_names(inner_values)

    assert sorted(result) == sorted(expected)
    assert "John" not in result
    assert "John Smith" in result

@patch("lorebinders.sort_names.data_cleaner.to_singular")
def test_sort_names_sort_shorter_longer_returns_no_match(mock_to_singular, sort_names):
    mock_to_singular.side_effect = ["banana", "apple"]
    result = sort_names._sort_shorter_longer("apple", "banana")
    assert result == ("apple", "banana")
    assert mock_to_singular.call_count == 2
    mock_to_singular.assert_has_calls([call("banana"), call("apple")])

@patch("lorebinders.sort_names.data_cleaner.to_singular")
def test_sort_names_sort_shorter_longer_handles_empty_strings(mock_to_singular, sort_names):
    mock_to_singular.side_effect = ["banana", ""]
    result = sort_names._sort_shorter_longer("", "banana")
    assert result == ("", "banana")
    assert mock_to_singular.call_count == 2
    mock_to_singular.assert_has_calls([call("banana"), call("")])

@patch("lorebinders.sort_names.data_cleaner.to_singular")
def test_sort_names_sort_shorter_longer_correct_first_singular(mock_to_singular, sort_names):
    mock_to_singular.return_value = "apple"
    result = sort_names._sort_shorter_longer("apple", "apples")
    assert result == ("apple", "apples")
    mock_to_singular.assert_called_once_with("apples")

@patch("lorebinders.sort_names.data_cleaner.to_singular")
def test_sort_names_sort_shorter_longer_correct_first_plural(mock_to_singular, sort_names):
    mock_to_singular.return_value = "apple"
    result = sort_names._sort_shorter_longer("apples", "apple")
    assert result == ("apple", "apples")
    assert mock_to_singular.call_count == 2
    mock_to_singular.assert_has_calls([call("apple"), call("apples")])

# split_and_update_lines tests
def test_sort_names_split_and_update_lines(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line1", "line2"], 1)
    sort_names._lines = ["line1 line2"]

    sort_names._split_and_update_lines(0, mock_split_func)

    assert sort_names._lines == ["line1", "line2"]


def test_sort_names_split_and_update_lines_empty_line(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = ([""], 0)
    sort_names._lines = [""]

    sort_names._split_and_update_lines(0, mock_split_func)

    assert sort_names._lines == [""]

def test_sort_names_split_and_update_lines_updates_lines_list_beginning_list(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line1", "line2"], 1)
    sort_names._lines = ["line1 line2", "line3", "line4"]

    sort_names._split_and_update_lines(0, mock_split_func)

    mock_split_func.assert_called_once_with("line1 line2")
    assert sort_names._lines == ["line1", "line2", "line3", "line4"]

def test_sort_names_split_and_update_lines_updates_lines_list_middle_list(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line2", "line3"], 1)
    sort_names._lines = ["line1", "line2 line3", "line4"]

    sort_names._split_and_update_lines(1, mock_split_func)

    mock_split_func.assert_called_once_with("line2 line3")
    assert sort_names._lines == ["line1", "line2", "line3", "line4"]


def test_sort_names_split_and_update_lines_updates_lines_list_end_list(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line3", "line4"], 1)
    sort_names._lines = ["line1", "line2", "line3 line4"]

    sort_names._split_and_update_lines(2, mock_split_func)

    mock_split_func.assert_called_once_with("line3 line4")
    assert sort_names._lines == ["line1", "line2", "line3", "line4"]

def test_sort_names_split_and_update_lines_correct_index(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line2", "line3"], 1)
    sort_names._lines = ["line1", "line2 line3", "line4"]

    sort_names._split_and_update_lines(1, mock_split_func)

    assert len(sort_names._lines) == 4
    assert sort_names._lines[1] == "line2"
    assert sort_names._lines[2] == "line3"
    assert sort_names._lines[3] == "line4"

def test_sort_names_split_and_update_lines_split_into_multiple_lines(sort_names):
    mock_split_func = Mock()
    mock_split_func.return_value = (["line2", "line3", "line4"], 2)
    sort_names._lines = ["line1", "line2 line3 line4", "line5"]

    sort_names._split_and_update_lines(1, mock_split_func)

    assert sort_names._lines == ["line1", "line2", "line3", "line4", "line5"]

# finalize_dict tests
@patch.object(SortNames, "_set_category_dict")
@patch.object(SortNames, "_build_ner_dict")
def test_sort_names_finalize_dict_with_category_name_and_dict(mock_build_ner_dict, mock_set_category_dict, sort_names):
    sort_names._category_name = "test_category"
    sort_names._inner_values = ["value1", "value2"]
    def set_category_dict_side_effect():
        sort_names._category_dict = {"test_category": ["value1", "value2"]}

    mock_set_category_dict.side_effect = set_category_dict_side_effect
    mock_build_ner_dict.return_value = {"test_category": ["value1", "value2"]}

    result = sort_names._finalize_dict()

    assert result == {"test_category": ["value1", "value2"]}
    mock_set_category_dict.assert_called_once()
    mock_build_ner_dict.assert_called_once()

@patch.object(SortNames, "_set_category_dict")
@patch.object(SortNames, "_build_ner_dict")
def test_sort_names_finalize_dict_no_category_name(mock_build_ner_dict, mock_set_category_dict, sort_names):
    sort_names._category_dict = {"test_category": ["value1", "value2"]}
    mock_build_ner_dict.return_value = {"test_category": ["value1", "value2"]}

    result =sort_names._finalize_dict()

    assert result == {"test_category": ["value1", "value2"]}
    mock_set_category_dict.assert_not_called()
    mock_build_ner_dict.assert_called_once()

# Tests for _process_remaining_modifications
@patch.object(SortNames, "_remove_parantheticals_pattern")
@patch.object(SortNames, "_has_narrator", return_value = False)
@patch.object(SortNames, "_has_bad_setting", return_value = False)
@patch.object(SortNames, "_has_odd_parentheses", return_value = True)
@patch.object(SortNames, "_remove_parentheses")
@patch.object(SortNames, "_replace_bad_setting")
def test_sort_names_process_remaining_modifications_odd_parentheses(mock_replace_bad_setting, mock_remove_parentheses, mock_has_odd_parentheses,  mock_has_bad_setting, mock_has_narrator, mock_remove_parantheticals_pattern, sort_names):
    mock_remove_parentheses.return_value = "Test line"
    mock_remove_parantheticals_pattern.return_value = "Test line"

    result = sort_names._process_remaining_modifications("Test (line")

    assert result == "Test line"
    mock_has_odd_parentheses.assert_called_once_with("Test (line")
    mock_remove_parentheses.assert_called_once_with("Test (line")
    mock_has_bad_setting.assert_called_once_with("Test line")
    mock_has_narrator.assert_called_once_with("Test line")
    mock_remove_parantheticals_pattern.assert_called_once_with("Test line")
    mock_replace_bad_setting.assert_not_called()
    mock_replace_bad_setting.assert_not_called()

@patch.object(SortNames, "_remove_parantheticals_pattern")
@patch.object(SortNames, "_has_narrator", return_value = False)
@patch.object(SortNames, "_has_bad_setting", return_value = True)
@patch.object(SortNames, "_has_odd_parentheses", return_value = False)
@patch.object(SortNames, "_remove_parentheses")
@patch.object(SortNames, "_replace_bad_setting")
def test_sort_names_process_remaining_modifications_bad_setting(mock_replace_bad_setting, mock_remove_parentheses, mock_has_odd_parentheses,  mock_has_bad_setting, mock_has_narrator, mock_remove_parantheticals_pattern, sort_names):
    mock_replace_bad_setting.return_value = "Settings:"
    mock_remove_parantheticals_pattern.return_value = "Settings:"

    result = sort_names._process_remaining_modifications("Places:")

    assert result == "Settings:"
    mock_has_odd_parentheses.assert_called_once_with("Places:")
    mock_has_bad_setting.assert_called_once_with("Places:")
    mock_replace_bad_setting.assert_called_once()
    mock_has_narrator.assert_called_once_with("Settings:")
    mock_remove_parantheticals_pattern.assert_called_once_with("Settings:")
    mock_remove_parentheses.assert_not_called()

@patch.object(SortNames, "_remove_parantheticals_pattern")
@patch.object(SortNames, "_has_narrator", return_value=True)
@patch.object(SortNames, "_has_bad_setting", return_value=False)
@patch.object(SortNames, "_has_odd_parentheses", return_value=False)
@patch.object(SortNames, "_remove_parentheses")
@patch.object(SortNames, "_replace_bad_setting")
def test_sort_names_process_remaining_modifications_has_narrator(mock_replace_bad_setting, mock_remove_parentheses, mock_has_odd_parentheses,  mock_has_bad_setting, mock_has_narrator, mock_remove_parantheticals_pattern, sort_names):
    mock_remove_parantheticals_pattern.return_value = "Kalia"

    result = sort_names._process_remaining_modifications("Narrator")

    assert result == "Kalia"
    mock_has_odd_parentheses.assert_called_once_with("Narrator")
    mock_has_bad_setting.assert_called_once_with("Narrator")
    mock_has_narrator.assert_called_once_with("Narrator")
    mock_remove_parantheticals_pattern.assert_called_once_with("Kalia")
    mock_remove_parentheses.assert_not_called()
    mock_replace_bad_setting.assert_not_called()

@patch.object(SortNames, "_remove_parantheticals_pattern")
@patch.object(SortNames, "_has_narrator", return_value=False)
@patch.object(SortNames, "_has_bad_setting", return_value=False)
@patch.object(SortNames, "_has_odd_parentheses", return_value=False)
@patch.object(SortNames, "_remove_parentheses")
@patch.object(SortNames, "_replace_bad_setting")
def test_sort_names_process_remaining_modifications_remove_parantheticals_pattern(mock_replace_bad_setting, mock_remove_parentheses, mock_has_odd_parentheses, mock_has_bad_setting, mock_has_narrator, mock_remove_parantheticals_pattern, sort_names):
    mock_remove_parantheticals_pattern.return_value = "Test line"

    result = sort_names._process_remaining_modifications("Test (line)")

    assert result == "Test line"
    mock_has_odd_parentheses.assert_called_once_with("Test (line)")
    mock_has_bad_setting.assert_called_once_with("Test (line)")
    mock_has_narrator.assert_called_once_with("Test (line)")
    mock_remove_parantheticals_pattern.assert_called_once_with("Test (line)")
    mock_remove_parentheses.assert_not_called()
    mock_replace_bad_setting.assert_not_called()

@patch.object(SortNames, "_remove_parantheticals_pattern")
@patch.object(SortNames, "_has_narrator", return_value=False)
@patch.object(SortNames, "_has_bad_setting", return_value=False)
@patch.object(SortNames, "_has_odd_parentheses", return_value=False)
@patch.object(SortNames, "_remove_parentheses")
@patch.object(SortNames, "_replace_bad_setting")
def test_sort_names_process_remaining_modifications_no_modifications(mock_replace_bad_setting, mock_remove_parentheses, mock_has_odd_parentheses, mock_has_bad_setting, mock_has_narrator, mock_remove_parantheticals_pattern, sort_names):
    mock_remove_parantheticals_pattern.return_value = "Test line"

    result = sort_names._process_remaining_modifications("Test line")

    assert result == "Test line"
    mock_has_odd_parentheses.assert_called_once_with("Test line")
    mock_has_bad_setting.assert_called_once_with("Test line")
    mock_has_narrator.assert_called_once_with("Test line")
    mock_remove_parantheticals_pattern.assert_called_once_with("Test line")
    mock_remove_parentheses.assert_not_called()
    mock_replace_bad_setting.assert_not_called()

# sort method tests

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_remove_list_formatting(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["1. line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    mock_remove_list_formatting.side_effect = ["line1", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["line1", "line2"]
    mock_replace_inverted_setting.side_effect = ["line1", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("1. line1"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("line1"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("line1"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("line1"), call("line2")])
    mock_needs_newline.assert_has_calls([call("line1"), call("line2")])
    mock_split_and_update_lines.assert_not_called()

    mock_remove_leading_colon_pattern.assert_has_calls([call("line1"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2")])
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_starts_with_location(mock_remove_list_formatting, mock_starts_with_location,  mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["exterior: line1, line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (exterior)", "line2 (exterior)", "line3"]}

    mock_remove_list_formatting.side_effect = ["exterior: line1, line2", "line1 (exterior)", "line2 (exterior)", "line3"]
    mock_starts_with_location.side_effect = [True, False, False, False]
    def split_and_update_lines_side_effect(*args):
        sort_names._lines = ["line1 (exterior)", "line2 (exterior)", "line3"]
    mock_split_and_update_lines.side_effect = split_and_update_lines_side_effect
    mock_lowercase_interior_exterior.side_effect = ["line1 (exterior)", "line2 (exterior)", "line3"]
    mock_replace_inverted_setting.side_effect = ["line1 (exterior)", "line2 (exterior)", "line3"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1 (exterior)", "line2 (exterior)", "line3"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1 (exterior)", "line2 (exterior)", "line3"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2", "line3"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call('exterior: line1, line2'), call('line1 (exterior)'), call('line2 (exterior)'), call('line3')])
    mock_starts_with_location.assert_has_calls([call("exterior: line1, line2"), call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_replace_inverted_setting.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_is_list_as_str.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_needs_newline.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_should_skip_line.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_process_remaining_modifications.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_add_to_dict.assert_has_calls([call("line1 (exterior)"), call("line2 (exterior)"), call("line3")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_lowercase_interior_exterior(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line1 (INTERIOR)", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (interior)", "line2"]}

    mock_remove_list_formatting.side_effect = ["line1 (INTERIOR)", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["line1 (interior)", "line2"]
    mock_replace_inverted_setting.side_effect = ["line1 (interior)", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1 (interior)", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1 (interior)", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1 (interior", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("line1 (INTERIOR)"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("line1 (INTERIOR)"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1 (INTERIOR)"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_needs_newline.assert_has_calls([call("line1 (interior)"), call("line2")])

    mock_split_and_update_lines.assert_not_called()
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_process_remaining_modifications.assert_has_calls([call("line1 (interior)"), call("line2")])

    mock_add_to_dict.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_replace_inverted_setting(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["interior (line1)", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (interior)", "line2"]}

    mock_remove_list_formatting.side_effect = ["interior (line1)", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["interior (line1)", "line2"]
    mock_replace_inverted_setting.side_effect = ["line1 (interior)", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1 (interior)", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1 (interior)", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1 (interior", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("interior (line1)"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("interior (line1)"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("interior (line1)"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("interior (line1)"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_needs_newline.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_split_and_update_lines.assert_not_called()
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_process_remaining_modifications.assert_has_calls([call("line1 (interior)"), call("line2")])

    mock_add_to_dict.assert_has_calls([call("line1 (interior)"), call("line2")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_split_at_commas(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line1, line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3"]}

    mock_remove_list_formatting.side_effect = ["line1, line2", "line1", "line2", "line3"]
    mock_starts_with_location.return_value = False
    def split_and_update_lines_side_effect(*args):
        sort_names._lines = ["line1", "line2", "line3"]
    mock_split_and_update_lines.side_effect = split_and_update_lines_side_effect
    mock_lowercase_interior_exterior.side_effect = ["line1, line2", "line1", "line2", "line3"]
    mock_replace_inverted_setting.side_effect = ["line1, line2", "line1", "line2", "line3"]
    mock_is_list_as_str.side_effect = [True, False, False, False]
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2", "line3"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2", "line3"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2", "line3"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("line1, line2"), call("line1"), call("line2"), call("line3")])
    mock_starts_with_location.assert_has_calls([call("line1, line2"), call("line1"), call("line2"), call("line3")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1, line2"), call("line1"), call("line2"), call("line3")])
    mock_replace_inverted_setting.assert_has_calls([call("line1, line2"), call("line1"), call("line2"), call("line3")])
    mock_is_list_as_str.assert_has_calls([call("line1, line2"), call("line1"), call("line2"), call("line3")])
    mock_needs_newline.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_split_and_update_lines.assert_called_once_with(0, sort_names._split_at_commas)
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_add_missing_newline(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines, mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line1 line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3"]}

    mock_remove_list_formatting.side_effect = ["line1 line2", "line1","line2", "line3"]
    mock_starts_with_location.return_value = False
    def split_and_update_lines_side_effect(index, func):
        if index == 0:
            sort_names._lines = ["line1", "line2", "line3"]
    mock_split_and_update_lines.side_effect = split_and_update_lines_side_effect
    mock_lowercase_interior_exterior.side_effect = ["line1 line2", "line1", "line2", "line3"]
    mock_replace_inverted_setting.side_effect = ["line1 line2", "line1", "line2", "line3"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.side_effect = [True, False, False, False]
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2", "line3"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2", "line3"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2", "line3"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    print(sort_names._lines)
    mock_remove_list_formatting.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_starts_with_location.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_replace_inverted_setting.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_is_list_as_str.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_needs_newline.assert_has_calls([call("line1 line2"), call("line1"), call("line2"), call("line3")])
    mock_split_and_update_lines.assert_called_once_with(0, sort_names._add_missing_newline)
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2"), call("line3")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_remove_leading_colon(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = [":line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    mock_remove_list_formatting.side_effect = [":line1", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = [":line1", "line2"]
    mock_replace_inverted_setting.side_effect = [":line1", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call(":line1"), call("line2")])
    mock_starts_with_location.assert_has_calls([call(":line1"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call(":line1"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call(":line1"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call(":line1"), call("line2")])
    mock_needs_newline.assert_has_calls([call(":line1"), call("line2")])
    mock_split_and_update_lines.assert_not_called()

    mock_remove_leading_colon_pattern.assert_has_calls([call(":line1"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2")])
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_should_skip_line(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["none", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line2"]}

    mock_remove_list_formatting.side_effect = ["none", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["none", "line2"]
    mock_replace_inverted_setting.side_effect = ["none", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["none", "line2"]
    mock_should_skip_line.side_effect = [True, False]
    mock_process_remaining_modifications.return_value = "line2"
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("none"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("none"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("none"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("none"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("none"), call("line2")])
    mock_needs_newline.assert_has_calls([call("none"), call("line2")])
    mock_split_and_update_lines.assert_not_called()

    mock_remove_leading_colon_pattern.assert_has_calls([call("none"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("none"), call("line2")])
    mock_process_remaining_modifications.assert_called_once_with("line2")
    mock_add_to_dict.assert_called_once_with("line2")
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_process_remaining_modifications(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line0", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    mock_remove_list_formatting.side_effect = ["line0", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["line0", "line2"]
    mock_replace_inverted_setting.side_effect = ["line0", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line0", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("line0"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("line0"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line0"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("line0"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("line0"), call("line2")])
    mock_needs_newline.assert_has_calls([call("line0"), call("line2")])
    mock_split_and_update_lines.assert_not_called()

    mock_remove_leading_colon_pattern.assert_has_calls([call("line0"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line0"), call("line2")])
    mock_process_remaining_modifications.assert_has_calls([call("line0"), call("line2")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2")])
    mock_finalize_dict.assert_called_once()

@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_no_modification(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines,  mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    mock_remove_list_formatting.side_effect = ["line1", "line2"]
    mock_starts_with_location.return_value = False
    mock_lowercase_interior_exterior.side_effect = ["line1", "line2"]
    mock_replace_inverted_setting.side_effect = ["line1", "line2"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.return_value = False
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    mock_remove_list_formatting.assert_has_calls([call("line1"), call("line2")])
    mock_starts_with_location.assert_has_calls([call("line1"), call("line2")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1"), call("line2")])
    mock_replace_inverted_setting.assert_has_calls([call("line1"), call("line2")])
    mock_is_list_as_str.assert_has_calls([call("line1"), call("line2")])
    mock_needs_newline.assert_has_calls([call("line1"), call("line2")])
    mock_split_and_update_lines.assert_not_called()

    mock_remove_leading_colon_pattern.assert_has_calls([call("line1"), call("line2")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2")])
    assert mock_process_remaining_modifications.call_count == 2
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2")])
    mock_finalize_dict.assert_called_once()


@patch.object(SortNames, "_finalize_dict")
@patch.object(SortNames, "_add_to_dict")
@patch.object(SortNames, "_process_remaining_modifications")
@patch.object(SortNames, "_should_skip_line")
@patch.object(SortNames, "_remove_leading_colon_pattern")
@patch.object(SortNames, "_needs_newline")
@patch.object(SortNames, "_is_list_as_str")
@patch.object(SortNames, "_replace_inverted_setting")
@patch.object(SortNames, "_lowercase_interior_exterior")
@patch.object(SortNames, "_split_and_update_lines")
@patch.object(SortNames, "_starts_with_location")
@patch.object(SortNames, "_remove_list_formatting")
def test_sort_add_missing_newline_in_middle(mock_remove_list_formatting, mock_starts_with_location, mock_split_and_update_lines, mock_lowercase_interior_exterior, mock_replace_inverted_setting,   mock_is_list_as_str, mock_needs_newline, mock_remove_leading_colon_pattern, mock_should_skip_line, mock_process_remaining_modifications, mock_add_to_dict, mock_finalize_dict, sort_names):
    sort_names._lines = ["line1", "line2 line3", "line4"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3", "line4"]}

    mock_remove_list_formatting.side_effect = ["line1", "line2 line3","line2", "line3", "line4"]
    mock_starts_with_location.return_value = False
    def split_and_update_lines_side_effect(index, func):
            sort_names._lines = ["line1", "line2", "line3", "line4"]
    mock_split_and_update_lines.side_effect = split_and_update_lines_side_effect
    mock_lowercase_interior_exterior.side_effect = ["line1", "line2 line3","line2", "line3", "line4"]
    mock_replace_inverted_setting.side_effect = ["line1", "line2 line3","line2", "line3", "line4"]
    mock_is_list_as_str.return_value = False
    mock_needs_newline.side_effect = [False, True, False, False, False]
    mock_remove_leading_colon_pattern.side_effect = ["line1", "line2", "line3", "line4"]
    mock_should_skip_line.return_value = False
    mock_process_remaining_modifications.side_effect = ["line1", "line2", "line3", "line4"]
    def _category_dict_side_effect(*args):
        sort_names._category_dict = {"Test": ["line1", "line2", "line3", "line4"]}
    mock_add_to_dict.side_effect = _category_dict_side_effect
    mock_finalize_dict.return_value = expected

    result = sort_names.sort()

    assert result == expected
    print(sort_names._lines)
    mock_remove_list_formatting.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_starts_with_location.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_lowercase_interior_exterior.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_replace_inverted_setting.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_is_list_as_str.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_needs_newline.assert_has_calls([call("line1"), call("line2 line3"), call("line2"), call("line3"), call("line4")])
    mock_split_and_update_lines.assert_called_once_with(1, sort_names._add_missing_newline)
    mock_remove_leading_colon_pattern.assert_has_calls([call("line1"), call("line2"), call("line3"), call("line4")])
    mock_should_skip_line.assert_has_calls([call("line1"), call("line2"), call("line3"), call("line4")])
    mock_process_remaining_modifications.assert_has_calls([call("line1"), call("line2"), call("line3"), call("line4")])
    mock_add_to_dict.assert_has_calls([call("line1"), call("line2"), call("line3"), call("line4")])
    mock_finalize_dict.assert_called_once()
