import pytest
from unittest.mock import Mock, patch

from lorebinders.name_tools.name_summarizer import NameSummarizer


def test_name_summarizer_init(ai_interface):
    summarizer = NameSummarizer(ai_interface)

    assert summarizer._ai == ai_interface
    assert summarizer.temperature == 0.4
    assert summarizer.max_tokens == 200
    assert summarizer._categories_base == ["Characters", "Settings"]
    assert summarizer.json_mode == False
    assert summarizer._single_role_script is None
    assert summarizer._current_category is None
    assert summarizer._current_name is None
    assert summarizer.lorebinder == {}



def test_name_summarizer_build_role_script(name_summarizer):
    name_summarizer.build_role_script()

    assert name_summarizer._single_role_script is not None
    assert name_summarizer._single_role_script.script == (
        "You are an expert summarizer. Please summarize the description "
        "over the course of the story for the following:"
    )
    assert name_summarizer._single_role_script.max_tokens == 200

def test_parse_response_valid_response_updates_lorebinder(name_summarizer):

    name_summarizer.lorebinder = {"Characters": {"Alice": {}}}
    name_summarizer._current_category = "Characters"
    name_summarizer._current_name = "Alice"
    response = "Alice is a brave warrior."

    result = name_summarizer._parse_response(response)

    assert result == {"Characters": {"Alice": {"summary": "Alice is a brave warrior."}}}

@patch("lorebinders.name_tools.name_summarizer.create_prompts")
@patch.object(NameSummarizer, "_get_ai_response")
@patch.object(NameSummarizer, "_parse_response")
def test_name_summarizer_identify_current_category_and_name(mock_parse_response, mock_get_ai_response, mock_create_prompts, name_summarizer):
    prompts = iter([
        ("Settings", "Castle", "Prompt 1"),
        ("Characters", "King", "Prompt 2")
    ])
    mock_create_prompts.return_value=prompts
    mock_get_ai_response.return_value = "AI response"
    mock_parse_response.return_value = {}
    lorebinder = {"test": "value"}

    name_summarizer._single_role_script = Mock()
    name_summarizer._get_ai_response = mock_get_ai_response
    name_summarizer._parse_response = mock_parse_response

    name_summarizer.summarize_names(lorebinder)

    assert name_summarizer._current_category == "Settings"
    assert name_summarizer._current_name == "Castle"
    next(prompts)
    assert name_summarizer._current_category == "Characters"
    assert name_summarizer._current_name == "King"
    assert name_summarizer._get_ai_response.call_count == 2
    assert name_summarizer._parse_response.call_count == 2


def test_name_summarizer_summary_added_to_correct_entry(name_summarizer, mock_lorebinder):
    name_summarizer._get_ai_response = Mock(return_value="AI response")

    result = name_summarizer.summarize_names(mock_lorebinder)

    for category in result:
        for name in result[category]:
            assert "summary" in result[category][name]
            assert result[category][name]["summary"] == "AI response"

def test_name_summarizer_handle_empty_or_none_responses(name_summarizer):
    lorebinder = {
        "Characters": {
            "Alice": {"summary": ""},
            "Bob": {"summary": None}
        },
        "Settings": {
            "Forest": {"summary": ""},
            "Castle": {"summary": None}
        }
    }

    result = name_summarizer.summarize_names(lorebinder)

    assert not result["Characters"]["Alice"]["summary"]
    assert not result["Characters"]["Bob"]["summary"]
    assert not result["Settings"]["Forest"]["summary"]
    assert not result["Settings"]["Castle"]["summary"]

@patch.object(NameSummarizer, "_get_ai_response")
def test_name_summarizer_new_summarize_names_returns_updated_lorebinder(mock_get_ai_response, name_summarizer, mock_lorebinder, mock_lorebinder_with_summary):
    mock_get_ai_response.return_value = "Generated response"
    name_summarizer._single_role_script = Mock()
    updated_lorebinder = name_summarizer.summarize_names(mock_lorebinder)
    assert updated_lorebinder == mock_lorebinder_with_summary

@patch.object(NameSummarizer, "_get_ai_response")
@patch('lorebinders.name_tools.name_summarizer.RoleScript')
def test_name_summarizer_get_ai_response(MockRoleScript, mock_get_ai_response, name_summarizer):
    prompt = "Test prompt"

    name_summarizer._get_ai_response(MockRoleScript, prompt)

    mock_get_ai_response.assert_called_once_with(MockRoleScript, prompt)

@patch("lorebinders.name_tools.name_summarizer.create_prompts")
@patch.object(NameSummarizer, "_get_ai_response")
@patch.object(NameSummarizer, "_parse_response")
def test_name_summarizer_summarize_names(mock_parse_response, mock_get_ai_response, mock_create_prompts, name_summarizer):
    """Test the summarize_names method with patches of the create_prompts function and the _get_ai_response and _parse_response methods"""

    prompts: list[tuple[str, str, str]] = [("Characters", "Alice", "Alice: Description1"), ("Settings", "Forest", "Forest: Description2")]
    mock_create_prompts.return_value = iter(prompts)
    mock_get_ai_response.return_value = "Generated summary"

    name_summarizer._single_role_script = Mock()
    name_summarizer._get_ai_response = mock_get_ai_response
    name_summarizer._parse_response = mock_parse_response

    name_summarizer.summarize_names({"test": "value"})

    assert mock_create_prompts.call_count == 1
    assert mock_get_ai_response.call_count == 2
    assert mock_parse_response.call_count == 2
