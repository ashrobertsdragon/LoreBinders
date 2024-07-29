import pytest
from unittest.mock import Mock, patch
from lorebinders.name_tools.name_extractor import create_instructions, build_custom_role, build_role_script, extract_names, parse_response


@pytest.fixture
def mock_parse_response():
    with patch("lorebinders.name_tools.name_extractor.parse_response") as mock:
        yield mock

@pytest.fixture
def MockRoleScript():
    with patch("lorebinders.name_tools.name_extractor.RoleScript") as mock:
        yield mock

@pytest.fixture
def MockSortNames():
    with patch("lorebinders.name_tools.name_extractor.SortNames") as mock:
        yield mock

@pytest.fixture
def mock_get_ai_response():
    with patch("lorebinders.name_tools.name_extractor.name_tools.get_ai_response") as mock:
        yield mock

def test_create_instructions():
    with patch("lorebinders.name_tools.name_tools.get_instruction_text") as mock_get_instruction_text:
        mock_get_instruction_text.side_effect = [
            "Mocked base instruction",
            "Mocked further instructions"
        ]

        base_instruction, further_instructions = create_instructions()

        assert base_instruction == "Mocked base instruction"
        assert further_instructions == "Mocked further instructions"

def test_build_custom_role_none():
    result = build_custom_role(None)
    assert result == ""

def test_build_custom_role_single_value():
    result = build_custom_role(["Category1"])
    expected = "Category1:Category11, Category12, Category13"
    assert result == expected

def test_build_custom_role_multiple_values():
    result = build_custom_role(["Category1", "Category2"])
    expected = "Category1:Category11, Category12, Category13\nCategory2:Category21, Category22, Category23"
    assert result == expected

def test_build_custom_role_empty_list():
    result = build_custom_role([])
    assert result == ""

@patch("lorebinders.name_tools.name_extractor.build_custom_role")
@patch("lorebinders.name_tools.name_extractor.create_instructions")
def test_build_role_script_no_custom_categories(mock_create_instructions, mock_build_custom_role, MockRoleScript):
    mock_create_instructions.return_value = ("base_instructions", "further_instructions")
    mock_build_custom_role.return_value = ""
    MockRoleScript.return_value = Mock()
    result = build_role_script(None)
    MockRoleScript.assert_called_once_with("base_instructions\nfurther_instructions\n", max_tokens=1000)

@patch("lorebinders.name_tools.name_extractor.build_custom_role")
@patch("lorebinders.name_tools.name_extractor.create_instructions")
def test_build_role_script_single_custom_category(mock_create_instructions, mock_build_custom_role, MockRoleScript):
    mock_create_instructions.return_value = ("base_instructions", "further_instructions")
    MockRoleScript.return_value = Mock()
    mock_build_custom_role.return_value = "category1"
    result = build_role_script(["category1"])
    MockRoleScript.assert_called_once_with("base_instructions\ncategory1\nfurther_instructions\ncategory1", max_tokens=1000)

@patch("lorebinders.name_tools.name_extractor.build_custom_role")
@patch("lorebinders.name_tools.name_extractor.create_instructions")
def test_build_role_script_multiple_custom_categories(mock_create_instructions, mock_build_custom_role, MockRoleScript):
    mock_create_instructions.return_value = ("base_instructions", "further_instructions")
    MockRoleScript.return_value = Mock()
    mock_build_custom_role.return_value = "category1, category2"
    result = build_role_script(["category1", "category2"])
    MockRoleScript.assert_called_once_with("base_instructions\ncategory1, category2\nfurther_instructions\ncategory1, category2", max_tokens=1000)

@patch("lorebinders.name_tools.name_extractor.build_custom_role")
@patch("lorebinders.name_tools.name_extractor.create_instructions")
def test_build_role_script_max_tokens(mock_create_instructions, mock_build_custom_role, MockRoleScript):
    mock_create_instructions.return_value = ("base_instructions", "further_instructions")
    MockRoleScript.return_value = Mock()
    mock_build_custom_role.return_value = ""
    result = build_role_script(None, 2000)
    MockRoleScript.assert_called_once_with("base_instructions\nfurther_instructions\n", max_tokens=2000)

def test_extract_names_with_narrator(MockRoleScript, mock_get_ai_response, mock_parse_response):
    mock_ai = Mock()
    mock_chapter = Mock()
    mock_chapter.text = "chapter content"
    MockRoleScript = Mock()
    mock_get_ai_response.return_value = "ai response"
    mock_parse_response.return_value = ["name1", "name2"]

    narrator = "narrator"
    result = extract_names(mock_ai, mock_chapter, MockRoleScript, narrator)
    assert result == ["name1", "name2"]
    mock_get_ai_response.assert_called_once_with(mock_ai, MockRoleScript, "Text: chapter content", 0.2, False)
    mock_parse_response.assert_called_once_with("ai response", "narrator")

def test_extract_names_without_narrator(MockRoleScript, mock_get_ai_response, mock_parse_response):
    mock_ai = Mock()
    mock_chapter = Mock()
    mock_chapter.text = "chapter content"
    MockRoleScript = Mock()
    mock_get_ai_response.return_value = "ai response"
    mock_parse_response.return_value = ["name1", "name2"]

    narrator = None
    result = extract_names(mock_ai, mock_chapter, MockRoleScript, None)
    assert result == ["name1", "name2"]
    mock_get_ai_response.assert_called_once_with(mock_ai, MockRoleScript, "Text: chapter content", 0.2, False)
    mock_parse_response.assert_called_once_with("ai response", None)

def test_parse_response_with_narrator(MockSortNames):
    mock_sorter = Mock()
    MockSortNames.return_value = mock_sorter
    mock_sorter.sort.return_value = {"category1": ["name1", "name2"]}

    result = parse_response("ai_response", "narrator")

    MockSortNames.assert_called_once_with("ai_response", "narrator")
    mock_sorter.sort.assert_called_once()
    assert result == {"category1": ["name1", "name2"]}

def test_parse_response_without_narrator(MockSortNames):
    mock_sorter = Mock()
    MockSortNames.return_value = mock_sorter
    mock_sorter.sort.return_value = {"category1": ["name1", "name2"]}

    result = parse_response("ai_response", None)

    MockSortNames.assert_called_once_with("ai_response", "")
    mock_sorter.sort.assert_called_once()
    assert result == {"category1": ["name1", "name2"]}
