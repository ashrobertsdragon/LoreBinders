from unicodedata import category
import pytest
from unittest.mock import Mock, patch, call

from lorebinders.name_tools.name_summarizer import build_role_script, summarize_names, update_lorebinder

@pytest.fixture
def mock_lorebinder():
    return {
    "Characters": {
        "John Doe": {
            "Chapter 1": "John Doe is introduced as a mysterious stranger.",
            "Chapter 2": "John Doe shows his skills in a challenging situation.",
            "Chapter 3": "John Doe faces a moral dilemma."
        },
        "Jane Smith": {
            "Chapter 1": "Jane Smith is introduced as a determined detective.",
            "Chapter 2": "Jane Smith uncovers a hidden secret.",
            "Chapter 3": "Jane Smith confronts her past."
        },
        "Bob Johnson": {
            "Chapter 1": "Bob Johnson is introduced as a retired soldier.",
            "Chapter 2": "Bob Johnson uses his military training to help the team.",
            "Chapter 3": "Bob Johnson makes a sacrifice for the greater good."
        }
    },
    "Settings": {
        "New York City": {
            "Chapter 1": "The story begins in the bustling streets of New York City.",
            "Chapter 2": "The characters explore the hidden underground of New York City.",
            "Chapter 3": "The climax of the story takes place in Times Square."
        },
        "London": {
            "Chapter 1": "The story starts in the historic streets of London.",
            "Chapter 2": "The characters visit the famous British Museum.",
            "Chapter 3": "The final showdown occurs in the Tower of London."
        },
        "Tokyo": {
            "Chapter 1": "The story unfolds in the neon-lit streets of Tokyo.",
            "Chapter 2": "The characters visit the famous Meiji Shrine.",
            "Chapter 3": "The conclusion of the story happens in the Shibuya Crossing."
        }
    }
}

@patch("lorebinders.name_tools.name_summarizer.RoleScript")
def test_build_role_script_default_max_tokens(MockRoleScript):

    build_role_script()
    MockRoleScript.assert_called_once_with("You are an expert summarizer. Please summarize the description over the course of the story for the following:", 200)

@patch("lorebinders.name_tools.name_summarizer.RoleScript")
def test_build_role_script_non_default_max_tokens(MockRoleScript):
    build_role_script(1000)
    MockRoleScript.assert_called_once_with("You are an expert summarizer. Please summarize the description over the course of the story for the following:", 1000)

def test_update_lorebinder():

    response = "AI generated summary"
    lorebinder = {
        "Characters": {
            "John Doe": {
                "Chapter 1": "John Doe is introduced as a mysterious stranger.",
                "Chapter 2": "John Doe shows his skills in a challenging situation.",
                "Chapter 3": "John Doe faces a moral dilemma.",
            }
        }
    }
    category = "Characters"
    name = "John Doe"

    result = update_lorebinder(response, lorebinder, category, name)

    assert result[category][name]["Summary"] == response
    assert result == {
        "Characters": {
            "John Doe": {
                "Chapter 1": "John Doe is introduced as a mysterious stranger.",
                "Chapter 2": "John Doe shows his skills in a challenging situation.",
                "Chapter 3": "John Doe faces a moral dilemma.",
                "Summary": "AI generated summary"
            }
        }
    }

@patch("lorebinders.name_tools.name_summarizer.prompt_generator.create_prompts")
@patch("lorebinders.name_tools.name_summarizer.name_tools.get_ai_response")
@patch("lorebinders.name_tools.name_summarizer.build_role_script")
@patch("lorebinders.name_tools.name_summarizer.update_lorebinder")
def test_summarize_names(mock_update_lorebinder, mock_build_role_script, mock_get_ai_response, mock_create_prompts):

    prompts: list[tuple[str, str, str]] = [("Characters", "Alice", "Alice: Description1"), ("Settings", "Forest", "Forest: Description2")]
    mock_create_prompts.return_value = iter(prompts)

    mock_get_ai_response.return_value = "Generated summary"
    mock_build_role_script.return_value = "Role script"
    mock_update_lorebinder.return_value = {"updated": "dictionary"}

    lorebinder = {"test": "value"}
    ai = "AIInterface"
    result = summarize_names(ai, lorebinder)

    mock_build_role_script.assert_called_once()
    mock_create_prompts.assert_called_once()

    assert mock_get_ai_response.call_count == 2
    assert mock_update_lorebinder.call_count == 2

    assert result == {"updated": "dictionary"}
