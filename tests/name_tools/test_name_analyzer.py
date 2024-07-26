import pytest
from unittest.mock import Mock, patch

from lorebinders.name_tools.name_analyzer import NameAnalyzer
from tests.name_tools.name_fixtures import name_analyzer, name_analyzer_markdown, mock_metadata, mock_chapter


def test_name_analyzer_init(name_analyzer):
    assert name_analyzer.instruction_type == "json"
    assert name_analyzer.temperature == 0.4
    assert name_analyzer.json_mode == True
    assert name_analyzer.absolute_max_tokens == 1000
    assert isinstance(name_analyzer.tokens_per, dict)

def test_name_analyzer_init_markdown(name_analyzer_markdown):
    assert name_analyzer_markdown.instruction_type == "markdown"
    assert name_analyzer_markdown.temperature == 0.4
    assert name_analyzer_markdown.json_mode == False
    assert name_analyzer_markdown.absolute_max_tokens == 1000
    assert isinstance(name_analyzer_markdown.tokens_per, dict)

def test_name_analyzer_get_tokens_per(name_analyzer):
    json_tokens = name_analyzer._get_tokens_per()
    assert json_tokens == {"Characters": 200, "Settings": 150, "Other": 100}

    name_analyzer.instruction_type = "markdown"
    markdown_tokens = name_analyzer._get_tokens_per()
    assert markdown_tokens == {"Characters": 170, "Settings": 127, "Other": 85}

def test_name_analyzer_base_instructions(name_analyzer):
    with patch.object(NameAnalyzer, '_get_instruction_text') as mock_get:
        mock_get.return_value = "Base instructions"
        assert name_analyzer.base_instructions == "Base instructions"
        mock_get.assert_called_once_with("name_analyzer_base_instructions.txt", prompt_type="json")

def test_name_analyzer_character_instructions(name_analyzer):
    with patch.object(NameAnalyzer, '_get_instruction_text') as mock_get:
        mock_get.return_value = "Character instructions"
        assert name_analyzer.character_instructions == "Character instructions"
        mock_get.assert_called_once_with("character_instructions.txt", prompt_type="json")

def test_name_analyzer_settings_instructions(name_analyzer):
    with patch.object(NameAnalyzer, '_get_instruction_text') as mock_get:
        mock_get.return_value = "Settings instructions"
        assert name_analyzer.settings_instructions == "Settings instructions"
        mock_get.assert_called_once_with("settings_instructions.txt", prompt_type="json")

def test_name_analyzer_initialize_chapter(name_analyzer, mock_metadata, mock_chapter):
    name_analyzer.initialize_chapter(mock_metadata, mock_chapter)
    assert name_analyzer.metadata == mock_metadata
    assert name_analyzer.chapter == mock_chapter
    assert name_analyzer._prompt == f"Text: {mock_chapter.text}"
    assert name_analyzer.custom_categories == mock_metadata.custom_categories
    assert name_analyzer.character_traits == mock_metadata.character_traits

def test_name_analyzer_generate_schema(name_analyzer):
    name_analyzer.character_traits = ["Motivation"]
    character_schema = name_analyzer._generate_schema("Characters")
    assert "Appearance" in character_schema
    assert "Motivation" in character_schema

    settings_schema = name_analyzer._generate_schema("Settings")
    assert "Appearance" in settings_schema
    assert "Relative location" in settings_schema

    other_schema = name_analyzer._generate_schema("Items")
    assert other_schema == '{"Items": "Description"}'


def test_name_analyzer_form_schema(name_analyzer, mock_metadata):
    name_analyzer.character_traits = mock_metadata.character_traits
    schema = name_analyzer._form_schema(["Characters", "Settings", "Items"])
    assert "Characters" in schema
    assert "Settings" in schema
    assert "Items" in schema


def test_name_analyzer_create_instructions(name_analyzer):
    name_analyzer._base_instructions = "Base"
    name_analyzer._character_instructions = "Character"
    name_analyzer._settings_instructions = "Settings"
    instructions = name_analyzer._create_instructions(["Characters", "Settings", "Items"])
    assert "Base" in instructions
    assert "Character" in instructions
    assert "Settings" in instructions
    assert "Items" in instructions
    assert "schema" in instructions
    assert all(part in instructions for part in ["Base", "Character", "Settings"])

@patch.object(NameAnalyzer, "_create_instructions")
@patch.object("NameAnalyzer","_form_schema")
def test_name_analyzer_create_role_script(mock_form_schema, mock_create_instructions, name_analyzer):
    mock_create_instructions.return_value="Test instructions"
    mock_form_schema.return_value="Test schema"
    role_script = name_analyzer._create_role_script(["Characters", "Settings"], 500)
    assert "Test instructions" in role_script.script
    assert "Test schema" in role_script.script
    assert role_script.max_tokens == 500

def test_name_analyzer_build_role_script(name_analyzer, mock_chapter):
    name_analyzer.chapter = mock_chapter
    name_analyzer.absolute_max_tokens = 400
    name_analyzer.tokens_per = {"Characters": 150, "Settings": 75, "Other": 50}

    with patch.object(NameAnalyzer, '_create_role_script', return_value=Mock()):
        name_analyzer.build_role_script()

        assert len(name_analyzer._role_scripts) == 2
        assert name_analyzer._create_role_script.call_count == 2


def test_name_analyzer_combine_responses_json(name_analyzer):
    name_analyzer.json_mode = True
    responses = ['{"a": 1}', '{"b": 2}']
    combined = name_analyzer._combine_responses(responses)
    assert combined == '{"a": 1,"b": 2}'

def test_name_analyzer_combine_responses_markdown(name_analyzer):
    name_analyzer.json_mode = False
    responses = ['# Part 1', '# Part 2']
    combined = name_analyzer._combine_responses(responses)
    assert combined == '# Part 1\n# Part 2'

@patch.object(NameAnalyzer, "_get_ai_response")
def test_name_analyzer_analyze_names(mock_get_ai_response, name_analyzer, mock_chapter):
    name_analyzer.chapter = mock_chapter
    name_analyzer._prompt = f"Text: {name_analyzer.chapter.text}"
    mock_get_ai_response.return_value = '{"test": "response"}'
    name_analyzer._role_scripts = [Mock(), Mock()]
    name_analyzer._parse_response = Mock(return_value={"parsed": "data"})
    result = name_analyzer.analyze_names()
    assert result == {"parsed": "data"}
    assert mock_get_ai_response.call_count == 2

@patch('lorebinders.json_tools.RepairJSON')
def test_name_analyzer_parse_response_json(MockRepairJSON, name_analyzer):
    name_analyzer.instruction_type = "json"
    mock_repair = MockRepairJSON.return_value
    mock_repair.json_str_to_dict.return_value = {"parsed": "data"}
    result = name_analyzer._parse_response('{"test": "response"}')
    assert result == {"parsed": "data"}

@patch('lorebinders.markdown_parser.markdown_to_dict')
def test_name_analyzer_parse_response_markdown(mock_markdown_to_dict, name_analyzer):
    name_analyzer.instruction_type = "markdown"
    mock_markdown_to_dict.return_value = {"parsed": "data"}
    result = name_analyzer._parse_response("# Test\nContent")
    assert result == {"parsed": "data"}
