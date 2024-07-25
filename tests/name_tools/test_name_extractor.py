import pytest
from unittest.mock import Mock, patch

from lorebinders.name_tools.name_extractor import NameExtractor
from tests.name_tools.fixtures import name_extractor, mock_metadata, mock_chapter

def test_name_extractor_initialize_chapter(name_extractor, mock_metadata, mock_chapter):
    name_extractor._get_instruction_text = Mock(side_effect=["Base instructions", "Further instructions"])
    name_extractor.initialize_chapter(mock_metadata, mock_chapter)

    assert name_extractor.metadata == mock_metadata
    assert name_extractor.chapter == mock_chapter
    assert name_extractor._prompt == f"Text: {mock_chapter.text}"
    assert name_extractor.narrator == "John"
    assert name_extractor.custom_categories == ["Location", "Item"]
    assert hasattr(name_extractor, '_base_instructions')
    assert hasattr(name_extractor, '_further_instructions')


def test_name_extractor_create_instructions(name_extractor):
    name_extractor._get_instruction_text = Mock(side_effect=["Base instructions", "Further instructions"])

    base, further = name_extractor._create_instructions()

    assert base == "Base instructions"
    assert further == "Further instructions"
    name_extractor._get_instruction_text.assert_any_call("name_extractor_sys_prompt.txt")
    name_extractor._get_instruction_text.assert_any_call("name_extractor_instructions.txt")

def test_name_extractor_build_custom_role(name_extractor):
    name_extractor.custom_categories = ["Location", "Item"]
    result = name_extractor._build_custom_role()
    expected = "Location:Location1, Location2, Location3\nItem:Item1, Item2, Item3"
    assert result == expected

def test_name_extractor_build_custom_role_empty(name_extractor):
    name_extractor.custom_categories = []
    result = name_extractor._build_custom_role()
    assert result == ""

@patch.object(NameExtractor, "_build_custom_role")
@patch('lorebinders.attributes.RoleScript')
def test_name_extractor_build_role_script(MockRoleScript, mock_build_custom_role, name_extractor):
    mock_build_custom_role.return_value = "Custom role"
    name_extractor._base_instructions = "Base"
    name_extractor._further_instructions = "Further"
    name_extractor.custom_categories = ["Category"]
    name_extractor.max_tokens = 1000

    name_extractor.build_role_script()

    expected_script = "Base\n['Category'].\nFurther\nCustom role"
    MockRoleScript.assert_called_once_with(expected_script, 1000)
    assert name_extractor._single_role_script == MockRoleScript.return_value

@patch.object(NameExtractor, "_get_ai_response")
@patch.object(NameExtractor, "_parse_response")
def test_name_extractor_extract_names(mock_parse_response, mock_get_ai_response, name_extractor):
    mock_get_ai_response.return_value = "AI response"
    mock_parse_response.return_value = {"characters": ["Alice", "Bob"]}
    name_extractor._single_role_script = Mock()
    name_extractor._prompt = "Test prompt"

    result = name_extractor.extract_names()

    mock_get_ai_response.assert_called_once_with(name_extractor._single_role_script, "Test prompt")
    mock_parse_response.assert_called_once_with("AI response")
    assert result == {"characters": ["Alice", "Bob"]}

@patch('lorebinders.attributes.SortNames')
def test_name_extractor_parse_response(MockSortNames, name_extractor):
    name_extractor.narrator = "John"
    mock_sorter = MockSortNames.return_value
    mock_sorter.sort.return_value = {"characters": ["Alice", "Bob"]}

    result = name_extractor._parse_response("Raw AI response")

    MockSortNames.assert_called_once_with("Raw AI response", "John")
    mock_sorter.sort.assert_called_once()
    assert result == {"characters": ["Alice", "Bob"]}
