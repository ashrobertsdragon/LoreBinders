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


def test_sort_names_missing_newline_patterns_missing_newline_before(sort_names):
    before_line = "testString:"

    expected_before_result = [
        "test\nString:",
        "testString:",
        "testString:"
    ]

    before_result = sort_names._missing_newline_patterns(before_line)
    assert before_result == expected_before_result


def test_sort_names_missing_newline_patterns_missing_newline_between(sort_names):
    between_line = "a (test) String"
    expected_between_line_result = [
        "a (test) String",
        "a (test)\nString",
        "a (test) String"
    ]

    between_result = sort_names._missing_newline_patterns(between_line)
    assert between_result == expected_between_line_result

def test_sort_names_lowercase_interior_exterior_converts_interior_to_lowercase(sort_names):
    line = "test (INTERIOR)"
    result = sort_names._lowercase_interior_exterior(line)
    assert result == "test (interior)"

def test_sort_names_lowercase_interior_exterior_converts_exterior_to_lowercase(sort_names):
    line = "test (EXTERIOR)"
    result = sort_names._lowercase_interior_exterior(line)
    assert result == "test (exterior)"

def test_sort_names_missing_newline_patterns_missing_newline_after(sort_names):
    after_line = "Test:string"
    expected_after_line_result = [
        "Test:string",
        "Test:string",
        "Test:\nstring"
    ]

    after_result = sort_names._missing_newline_patterns(after_line)
    assert after_result == expected_after_line_result

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (" : test", "test"),
        (": test", "test"),
        (":test", ":test"),
        ("test", "test"),
        ("test:", "test:"),
        ("test : ", "test : "),
        ("test : test", "test:test"),
        ("test :test", "test : test"),
        ("test: test", "test:test"),
        ("test  :  test", "test:test"),
        ("test:  test", "test:test"),

    ]
)
def test_sort_names_remove_leading_colon(line, expected, sort_names):
    result = sort_names._remove_leading_colon_pattern(line)
    assert result == expected

def test_sort_names_replace_inverted_setting_exterior(sort_names):
    line = "exterior (test)"
    result = sort_names._replace_inverted_setting(line)
    assert result == "test (exterior)"

def test_sort_names_replace_inverted_setting_interior(sort_names):
    line = "interior (test)"
    result = sort_names._replace_inverted_setting(line)
    assert result == "test (interior)"

def test_sort_names_remove_parantheticals(sort_names):
    line = "test (test)"
    result = sort_names._remove_parantheticals_pattern(line)
    assert result == "test"

def test_add_missing_newline_missing_newline_before(sort_names):
    result = sort_names._add_missing_newline("testString:")
    assert result == ("""
test
String:""", 1
    )

def test_add_missing_newline_missing_newline_after(sort_names):
    result = sort_names._add_missing_newline("Test:string")
    assert result == ("""
Test:
string""", 1
    )

def test_add_missing_newline_missing_newline_between(sort_names):
    result = sort_names._add_missing_newline("a (test) String")
    assert result == ("""
a (test)
String""", 1
    )

def test_sort_names_split_at_commas(sort_names):
    line = "test, test, test"
    expected_result = ["test", "test", "test"]
    result = sort_names._split_at_commas(line)
    assert result == expected_result, 2

def test_sort_names_split_settings_line(sort_names):
    line = "interior: test, test, test"
    expected_result = ["test (interior)", "test (interior)", "test (interior)"]
    result = sort_names._split_settings_line(line)
    assert result == expected_result, 2

@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("", False), ("test test test", False),
        ("additional test test", True), ("test additional test", True),
        ("test test additional", True), ("note test test", True),
        ("test note test", True), ("test test note", True),
        ("none test test", True), ("test none test", True),
        ("test test none", True), ("mentioned test test", True),
        ("test mentioned test", True), ("test test mentioned", True),
        ("unknown test test", True), ("test unknown test", True),
        ("test test unknown", True), ("he test test", True),
        ("test he test", True), ("test test he", True),
        ("they test test", True), ("test they test", True),
        ("test test they", True), ("she test test", True),
        ("test she test", True), ("test test she", True),
        ("we test test", True), ("test we test", True),
        ("test test we", True), ("it test test", True),
        ("test it test", True), ("test test it", True),
        ("boy test test", True), ("test boy test", True),
        ("test test boy", True), ("girl test test", True),
        ("test girl test", True), ("test test girl", True),
        ("main test test", True), ("test main test", True),
        ("test test main", True), ("him test test", True),
        ("test him test", True), ("test test him", True),
        ("her test test", True), ("test her test", True),
        ("test test her", True), ("I test test", True),
        ("test I test", True), ("test test I", True),
        ("</s> test test", True), ("test </s> test", True),
        ("test test </s>", True), ("a test test", True),
        ("test a test", True), ("test test a", True),
        ("Additional test test", True), ("Test test a", True),
        ("test Additional test", True), ("test test Additional", True),
        ("Note test test", True), ("test Note test", True),
        ("test test Note", True), ("None test test", True),
        ("test None test", True), ("test test None", True),
        ("Mentioned test test", True), ("test Mentioned test", True),
        ("test test Mentioned", True), ("Unknown test test", True),
        ("test Unknown test", True), ("test test Unknown", True),
        ("He test test", True), ("test He test", True),
        ("test test He", True), ("They test test", True),
        ("test They test", True), ("test test They", True),
        ("She test test", True), ("test She test", True),
        ("test test She", True), ("We test test", True),
        ("test We test", True), ("test test We", True),
        ("It test test", True), ("test It test", True),
        ("test test It", True), ("Boy test test", True),
        ("test Boy test", True), ("test test Boy", True),
        ("Girl test test", True), ("test Girl test", True),
        ("test test Girl", True), ("Main test test", True),
        ("test Main test", True), ("test test Main", True),
        ("Him test test", True), ("test Him test", True),
        ("test test Him", True), ("Her test test", True),
        ("test Her test", True), ("test test Her", True),
        ("I test test", True), ("test I test", True),
        ("test test I", True), ("</s> test test", True),
        ("test </s> test", True), ("test test </s>", True),
        ("A test test", True), ("test A test", True),
        ("test test A", True), ("additional Test test", True),
        ("Test additional est", True), ("Test test additional", True),
        ("note Test test", True), ("Test note test", True),
        ("Test test note", True), ("none Test test", True),
        ("Test none test", True), ("Test test none", True),
        ("mentioned Test test", True), ("Test mentioned test", True),
        ("Test test mentioned", True), ("unknown Test test", True),
        ("Test unknown test", True), ("Test test unknown", True),
        ("he Test test", True), ("Test he Test", True),
        ("Test test he", True), ("they Test test", True),
        ("Test they test", True), ("Test test they", True),
        ("she Test test", True), ("Test she test", True),
        ("Test test she", True), ("we Test test", True),
        ("Test we test", True), ("Test test we", True),
        ("it Test test", True), ("Test it test", True),
        ("Test test it", True), ("boy Test test", True),
        ("Test boy test", True), ("Test test boy", True),
        ("girl Test test", True), ("Test girl test", True),
        ("Test test girl", True), ("main Test test", True),
        ("Test main test", True), ("Test test main", True),
        ("him Test test", True), ("Test him test", True),
        ("Test test him", True), ("her Test test", True),
        ("Test her test", True), ("Test test her", True),
        ("i Test test", True), ("Test i test", True),
        ("Test test i", True), ("</s> Test test", True),
        ("Test </s> test", True), ("Test test </s>", True),
        ("a Test test", True), ("Test a test", True)
    ]
)
def test_sort_names_should_skip_line(line, expected, sort_names):
    result = sort_names._should_skip_line(line)
    assert result == expected

def test_add_to_dict_category(sort_names):
    line = "Category:"

    sort_names._add_to_dict(line)

    assert sort_names._category_name == "Category"
    assert sort_names._inner_values == []
    assert sort_names._category_dict == {}

def test_add_to_dict_inner_value_without_category(sort_names):
    line = "Item"

    sort_names._add_to_dict(line)

    assert sort_names._category_name == ""
    assert sort_names._inner_values == ["Item"]
    assert sort_names._category_dict == {}

def test_sort_names_add_to_dict_sets_category_dict_one_value(sort_names):
    sort_names._category_name = "Category1"
    line1 = "test"
    line2 = "Category2:"

    sort_names._add_to_dict(line1)
    sort_names._add_to_dict(line2)

    assert sort_names._category_dict == {"Category": ["test"]}
    assert sort_names._inner_values == []

def test_sort_names_add_to_dict_sets_category_dict_multiple_values(sort_names):
    sort_names._category_name = "Category1"
    line1 = "test1"
    line2 = "test2"
    line3 = "test3"
    line4 = "Category2:"

    sort_names._add_to_dict(line1)
    sort_names._add_to_dict(line2)
    sort_names._add_to_dict(line3)
    sort_names._add_to_dict(line4)

    assert sort_names._category_dict == {"Category": ["test1", "test2", "test3"]}
    assert sort_names._inner_values == []


def test_sort_names_build_ner_dict_singular_and_plural_keys(sort_names):
    sort_names._category_dict = {
        "apples": ["apple1"],
        "orange": ["orange1"],
        "banana": ["banana1"],
        "apple": ["apple2"],
        "pear": ["pear1"]
    }
    expected_ner_dict = {
        "apple": ["apple1, apple2"],
        "orange": ["orange"],
        "banana": ["banana"],
        "pear": ["pear"]
    }

    sort_names._build_ner_dict()

    assert sort_names.ner_dict == expected_ner_dict

def test_sort_names_build_ner_dict_unique_categories(mock_compare_names, sort_names):

    sort_names._category_dict = {
        "category1": ["name1", "name2"],
        "category2": ["name1", "name2"]
    }

    sort_names._build_ner_dict()

    assert sort_names.ner_dict == {
        "category1": ["name1", "name2"],
        "category2": ["name1", "name2"]
    }

def test_sort_names_build_ner_dict_plural_no_singular(sort_names):

    sort_names._category_dict = {
        "categories": ["name1", "name2"],
        "other_category": ["name3", "name4"]
    }

    sort_names._build_ner_dict()

    assert sort_names.ner_dict == {
        "categories": ["name1", "name2"],
        "other_category": ["name3", "name4"]
    }

def test_sort_names_compare_names_single_set_of_names(sort_names):
    inner_values = ["Dr. John", "Mr. John Smith"]
    expected = ["John Smith"]
    result = sort_names._compare_names(inner_values)
    assert result == expected

def test_sort_names_compare_names_multiple_item_list(sort_names):
    inner_values = ["Dr. John", "John Smith", "Ms. Jane Doe", "J. Doe"]
    expected = ["John Smith", "Jane Doe"]
    result = sort_names._compare_names(inner_values)
    assert sorted(result) == sorted(expected)

def test_sort_names_compare_names_empty_list(sort_names):
    inner_values = []
    expected = []
    result = sort_names._compare_names(inner_values)
    assert result == expected

def test_sort_names_compare_names_remove_titles_from_names(sort_names):

    inner_values = ["Dr. John", "Mr. John Smith"]

    result = sort_names._compare_names(inner_values)

    assert "Mr. John Smith" not in result
    assert "Dr. John" not in result

def test_sort_names_compare_names_apply_name_map_to_each_name(sort_names):
    inner_values = ["Dr. John", "Mr. John Smith", "Ms. Jane"]
    expected = ["John Smith", "Jane"]

    result = sort_names._compare_names(inner_values)

    assert sorted(result) == sorted(expected)
    assert "John" not in result
    assert "John Smith" in result

def test_sort_names_sort_shorter_longer_returns_no_match(sort_names):
    result = sort_names._sort_shorter_longer("apple", "banana")
    assert result == ("apple", "banana")

def test_sort_names_sort_shorter_longer_handles_empty_strings(sort_names):
    result = sort_names._sort_shorter_longer("", "banana")
    assert result == ("", "banana")

def test_sort_names_sort_shorter_longer_correct_first_singular(sort_names):
    result = sort_names._sort_shorter_longer("apple", "apples")
    assert result == ("apple", "apples")

def test_sort_names_sort_shorter_longer_correct_first_plural(sort_names):
    result = sort_names._sort_shorter_longer("apples", "apple")
    assert result == ("apple", "apples")

def test_sort_names_split_and_update_lines_call_add_missing_newline_before(sort_names):
    sort_names._lines = ["lineALine:"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["lineA", "Lineb"]
    assert result == 1

def test_sort_names_split_and_update_lines_call_add_missing_newline_between(sort_names):
    sort_names._lines = ["lineA (test) lineB"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["lineA (test)", "lineB"]
    assert result == 1

def test_sort_names_split_and_update_lines_call_add_missing_newline_after(sort_names):
    sort_names._lines = ["lineA: lineB"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["lineA:", "lineB"]
    assert result == 1

def test_sort_names_split_and_update_lines_call_split_at_commas(sort_names):
    sort_names._lines = ["line 1, line2"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["line1", "line2"]
    assert result == 1

def test_sort_names_split_and_update_lines_call_split_at_commas_multiple(sort_names):
    sort_names._lines = ["line 1, line2, line3"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["line1", "line2", "line3"]
    assert result == 2

def test_sort_names_split_and_update_lines_call_split_settings_line(sort_names):
    sort_names._lines = ["Interior: line 1, line2"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["line1 (interior)", "line2 (interior)"]
    assert result == 1

def test_sort_names_split_and_update_lines_call_split_settings_line_multiple(sort_names):
    sort_names._lines = ["Interior: line 1, line2, line3"]
    result = sort_names._split_and_update_lines(0, sort_names._add_missing_newline)
    assert sort_names._lines == ["line1 (interior)", "line2 (interior)", "line3 (interior)"]
    assert result == 1

def test_sort_names_finalize_dict_with_category_name(sort_names):
    sort_names._category_name = "test_category"
    sort_names._inner_values = ["value1", "value2"]

    sort_names._finalize_dict()

    assert sort_names._category_dict == {"test_category": ["value1", "value2"]}
    assert dict(sort_names.ner_dict) == {"test_category": ["value1", "value2"]}

def test_sort_names_finalize_dict_no_category_name(sort_names):
    sort_names._category_dict = {"test_category": ["value1", "value2"]}

    sort_names._finalize_dict()

    assert dict(sort_names.ner_dict) == {"test_category": ["value1", "value2"]}

def test_sort_names_process_remaining_modifications_odd_parentheses(sort_names):
    result = sort_names._process_remaining_modifications("Test (line")
    assert result == "Test line"

def test_sort_names_process_remaining_modifications_bad_setting(sort_names):
    result = sort_names._process_remaining_modifications("Places:")
    assert result == "Settings:"

def test_sort_names_process_remaining_modifications_has_narrator(sort_names):
    result = sort_names._process_remaining_modifications("Narrator")
    assert result == "Kalia"

def test_sort_names_process_remaining_modifications_remove_parantheticals_pattern(sort_names):
    result = sort_names._process_remaining_modifications("Test (line)")
    assert result == "Test line"

def test_sort_names_process_remaining_modifications_no_modifications(sort_names):
    result = sort_names._process_remaining_modifications("Test line")
    assert result == "Test line"

def test_sort_remove_list_formatting(sort_names):
    sort_names._lines = ["1. line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_starts_with_location(sort_names):
    sort_names._lines = ["exterior: line1, line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (exterior)", "line2 (exterior)", "line3"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_lowercase_interior_exterior(sort_names):
    sort_names._lines = ["line1 (INTERIOR)", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (interior)", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_replace_inverted_setting(sort_names):
    sort_names._lines = ["interior (line1)", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1 (interior)", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_split_at_commas(sort_names):
    sort_names._lines = ["line1, line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_add_missing_newline(sort_names):
    sort_names._lines = ["line1 line2", "line3"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_remove_leading_colon(sort_names):
    sort_names._lines = [":line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_should_skip_line(sort_names):
    sort_names._lines = ["none", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_process_remaining_modifications(sort_names):
    sort_names._lines = ["line0", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_no_modification(sort_names):
    sort_names._lines = ["line1", "line2"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2"]}

    result = sort_names.sort()

    assert result == expected

def test_sort_add_missing_newline_in_middle(sort_names):
    sort_names._lines = ["line1", "line2 line3", "line4"]
    sort_names._category_name = "Test"
    expected = {"Test": ["line1", "line2", "line3", "line4"]}

    result = sort_names.sort()

    assert result == expected
