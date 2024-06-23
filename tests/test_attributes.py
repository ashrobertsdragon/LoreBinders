from dataclasses import dataclass
from pydantic import Field


from _types import AIModels, BookDict
from ai.ai_interface import AIModelConfig
from data_cleaner import ManipulateData
from json_tools import RepairJSON

import pytest
from unittest.mock import MagicMock

from src.lorebinders.attributes import (
    NameTools,
    NameExtractor,
    NameAnalyzer,
    NameSummarizer,
    RoleScript,
)

data = ManipulateData()
json_repair_tool = RepairJSON()


@dataclass
class MockAIModels:
    provider: str = "mock_provider"
    models: AIModels = Field(default_factory=AIModels)


@pytest.fixture
def mock_ai_models():
    return MockAIModels()


@pytest.fixture
def mock_ai_config(mock_ai_models):
    return AIModelConfig(mock_ai_models)


@pytest.fixture
def mock_ai_interface():
    return MagicMock(
        set_model=lambda model_config, model_id: None,
        create_payload=lambda prompt, role_script, temperature, max_tokens: {
            "model_name": "Mock Model",
            "prompt": prompt,
            "temperature": temperature,
            "role_script": role_script.script,
            "max_tokens": role_script.max_tokens,
        },
        call_api=lambda api_payload, json_response: "Mock Response",
    )


@pytest.fixture
def name_tools(mock_ai_models, mock_ai_interface):
    name_tools = NameTools(mock_ai_models)
    name_tools._ai = mock_ai_interface
    return name_tools


@pytest.fixture
def mock_chapter():
    return MagicMock(
        text="Test Chapter Text",
        names={"Characters": {"Character1": {"Thoughts": "Thinking"}}},
    )


@pytest.fixture
def mock_book_dict():
    return BookDict(
        title="Test Book",
        author="Test Author",
        book_file="test.txt",
        narrator="Test Narrator",
        character_traits=["Thoughts", "Actions"],
        custom_categories=["Events", "Places"],
    )


@pytest.fixture
def name_extractor(mock_ai_models, mock_chapter, mock_book_dict):
    name_extractor = NameExtractor(mock_ai_models)
    name_extractor.initialize_chapter(mock_book_dict, mock_chapter)
    return name_extractor


@pytest.fixture
def name_analyzer(mock_ai_models, mock_chapter, mock_book_dict):
    name_analyzer = NameAnalyzer(mock_ai_models)
    name_analyzer.initialize_chapter(mock_book_dict, mock_chapter)
    return name_analyzer


@pytest.fixture
def name_summarizer(mock_ai_models):
    return NameSummarizer(mock_ai_models)


def test_name_tools_init(name_tools, mock_ai_config, mock_ai_interface):
    assert name_tools._ai_config == mock_ai_config
    assert name_tools._ai == mock_ai_interface


def test_name_tools_get_ai_response(name_tools, mock_ai_interface):
    role_script = RoleScript(script="Test Script", max_tokens=100)
    prompt = "Test Prompt"
    model_id = 1
    response = name_tools._get_ai_response(role_script, prompt, model_id)
    mock_ai_interface.set_model.assert_called_once_with(
        name_tools._ai_config, model_id
    )
    mock_ai_interface.create_payload.assert_called_once_with(
        prompt, "Test Script", 100
    )
    mock_ai_interface.call_api.assert_called_once_with(
        {
            "model_name": "Mock Model",
            "prompt": "Test Prompt",
            "temperature": 1.0,
            "role_script": "Test Script",
            "max_tokens": 100,
        },
        False,
    )
    assert response == "Mock Response"


def test_name_tools_combine_responses(name_tools):
    responses = ['{"test": "value1"}', '{"test": "value2"}']
    combined_response = name_tools._combine_responses(responses)
    assert combined_response == '{"test": "value1", "test": "value2"}'


def test_name_extractor_init(name_extractor, mock_ai_models):
    assert name_extractor._ai_config.provider == "mock_provider"
    assert name_extractor.max_tokens == 1000
    assert name_extractor.temperature == 0.2


def test_name_extractor_build_custom_role_no_custom_categories(name_extractor):
    name_extractor.custom_categories = []
    assert name_extractor._build_custom_role() == ""


def test_name_extractor_build_custom_role_with_custom_categories(
    name_extractor,
):
    assert (
        name_extractor._build_custom_role()
        == "Events:Events1, Events2, Events3\nPlaces:Places1, Places2, Places3"
    )


def test_name_extractor_build_role_script(name_extractor, mock_chapter):
    name_extractor.build_role_script()
    assert name_extractor._single_role_script.script == (
        "You are a script supervisor compiling a list of characters in each scene. For the following selection, determine who are the characters, giving only their name and no other information. Please also determine the settings, both interior (e.g. ship's bridge, classroom, bar) and exterior (e.g. moon, Kastea, Hell's Kitchen).Events, Places.\nIf the scene is written in the first person, try to identify the narrator by their name. If you can't determine the narrator's identity. List 'Narrator' as a character. Use characters' names instead of their relationship to the narrator (e.g. 'Uncle Joe' should be 'Joe'. If the character is only identified by their relationship to the narrator (e.g. 'Mom' or 'Grandfather'), list the character by that identifier instead of the relationship (e.g. 'Mom' instead of 'Narrator's mom' or 'Grandfather' instead of 'Kalia's Grandfather'\nBe as brief as possible, using one or two words for each entry, and avoid descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris field of leftover asteroid pieces' should be 'Asteroid debris field'. 'Unmarked section of wall (potentially a hidden door)' should be 'unmarked wall section'\nDo not use these examples unless they actually appear in the text.\nIf you cannot find any mention of a specific category in the text, please respond with 'None found' on the same line as the category name. If you are unsure of a setting or no setting is shown in the text, please respond with 'None found' on the same line as the word 'Setting'\nPlease format the output exactly like this:\nCharacters:\ncharacter1\ncharacter2\ncharacter3\nSettings:\nSetting1 (interior)\nSetting2 (exterior)\nEvents:Events1, Events2, Events3\nPlaces:Places1, Places2, Places3"
    )
    assert name_extractor._single_role_script.max_tokens == 1000


def test_name_extractor_extract_names(name_extractor, mock_ai_interface):
    mock_ai_interface.call_api.return_value = '{"Characters": {"Character1": "Character1"}, "Settings": {"Setting1": "Setting1"}, "Events": {"Event1": "Event1"}, "Places": {"Place1": "Place1"}}'
    names = name_extractor.extract_names()
    mock_ai_interface.set_model.assert_called_once_with(
        name_extractor._ai_config, 1
    )
    mock_ai_interface.create_payload.assert_called_once_with(
        f"Text: {name_extractor.chapter.text}",
        name_extractor._single_role_script.script,
        name_extractor._single_role_script.max_tokens,
    )
    mock_ai_interface.call_api.assert_called_once_with(
        {
            "model_name": "Mock Model",
            "prompt": f"Text: {name_extractor.chapter.text}",
            "temperature": 1.0,
            "role_script": name_extractor._single_role_script.script,
            "max_tokens": 1000,
        },
        False,
    )
    assert names == {
        "Characters": {"Character1": "Character1"},
        "Settings": {"Setting1": "Setting1"},
        "Events": {"Event1": "Event1"},
        "Places": {"Place1": "Place1"},
    }


def test_name_extractor_parse_response(name_extractor, mock_chapter):
    response = '{"Characters": {"Character1": "Character1"}, "Settings": {"Setting1": "Setting1"}, "Events": {"Event1": "Event1"}, "Places": {"Place1": "Place1"}}'
    names = name_extractor._parse_response(response)
    assert names == {
        "Characters": {"Character1": "Character1"},
        "Settings": {"Setting1": "Setting1"},
        "Events": {"Event1": "Event1"},
        "Places": {"Place1": "Place1"},
    }


def test_name_analyzer_init(name_analyzer, mock_ai_models):
    assert name_analyzer._ai_config.provider == "mock_provider"
    assert name_analyzer.temperature == 0.4
    assert name_analyzer.ABSOLUTE_MAX_TOKENS == 4096
    assert name_analyzer.tokens_per == {
        "Characters": 200,
        "Settings": 150,
        "Other": 100,
    }


def test_name_analyzer_generate_schema_characters(name_analyzer):
    schema = name_analyzer._generate_schema("Characters")
    assert (
        schema
        == '{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description", "Thoughts": "Description", "Actions": "Description"}}'
    )


def test_name_analyzer_generate_schema_settings(name_analyzer):
    schema = name_analyzer._generate_schema("Settings")
    assert (
        schema
        == '{"Settings": {"Appearance": "Description", "Relative location": "Description", "Familiarity for main character": "Description"}}'
    )


def test_name_analyzer_generate_schema_other(name_analyzer):
    schema = name_analyzer._generate_schema("Events")
    assert schema == '{"Events": "Description"}'


def test_name_analyzer_create_instructions(name_analyzer):
    name_analyzer._to_batch = ["Characters", "Settings", "Events"]
    instructions = name_analyzer._create_instructions()
    assert instructions == (
        'You are a developmental editor helping create a story bible. \nBe detailed but concise, using short phrases instead of sentences. Do not justify your reasoning or provide commentary, only facts. Only one category per line, just like in the schema below, but all description for that category should be on the same line. If something appears to be miscatagorized, please put it under the correct category. USE ONLY STRINGS AND JSON OBJECTS, NO JSON ARRAYS. The output must be valid JSON.\nIf you cannot find any mention of something in the text, please respond with \'None found\' as the description for that category.\nFor each character in the chapter, describe their appearance, personality, mood, and relationships to other characters\nAn example from an early chapter of Jane Eyre:\n"Jane Eyre": {"Appearance": "Average height, slender build, fair skin, dark brown hair, hazel eyes, plain appearance", "Personality": "Reserved, self-reliant, modest", "Mood": "Angry at her aunt about her treatment while at Gateshead"}\nFor each setting in the chapter, note how the setting is described, where it is in relation to other locations and whether the characters appear to be familiar or unfamiliar with the location. Be detailed but concise.\nIf you are unsure of a setting or no setting is shown in the text, please respond with \'None found\' as the description for that setting.\nHere is an example from Wuthering Heights:\n"Moors": {"Appearance": Expansive, desolate, rugged, with high winds and craggy rocks", "Relative location": "Surrounds Wuthering Heights estate", "Main character\'s familiarity": "Very familiar, Catherine spent significant time roaming here as a child and represents freedom to her"}\nProvide descriptions of Events without referencing specific characters or plot points\nYou will format this information as a JSON object using the following schema where "description" is replaced with the actual information.\n'
    )


def test_name_analyzer_form_schema(name_analyzer):
    name_analyzer._to_batch = ["Characters", "Settings", "Events"]
    schema = name_analyzer._form_schema()
    assert (
        schema
        == '{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description", "Thoughts": "Description", "Actions": "Description"}}{"Settings": {"Appearance": "Description", "Relative location": "Description", "Familiarity for main character": "Description"}}{"Events": "Description"}'
    )


def test_name_analyzer_reset_variables(name_analyzer):
    name_analyzer._reset_variables("Characters", 200)
    assert name_analyzer._to_batch == ["Characters"]
    assert name_analyzer.max_tokens == 200


def test_name_analyzer_append_attributes_batch(name_analyzer):
    name_analyzer._to_batch = ["Characters", "Settings"]
    name_analyzer.max_tokens = 300
    instructions = "Test Instructions"
    name_analyzer._append_attributes_batch(instructions)
    assert name_analyzer._attributes_batch == [
        (
            '{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description", "Thoughts": "Description", "Actions": "Description"}}{"Settings": {"Appearance": "Description", "Relative location": "Description", "Familiarity for main character": "Description"}}',
            300,
            "Test Instructions",
        )
    ]


def test_name_analyzer_build_role_script(name_analyzer, mock_chapter):
    name_analyzer.build_role_script()
    assert name_analyzer._role_scripts == [
        RoleScript(
            script=(
                "You are a developmental editor helping create a story bible. \n"
                "Be detailed but concise, using short phrases instead of "
                "sentences. Do not justify your reasoning or provide "
                "commentary, only facts. Only one category per line, just "
                "like in the schema below, but all description for that "
                "category should be on the same line. If something appears "
                "to be miscatagorized, please put it under the correct "
                "category. USE ONLY STRINGS AND JSON OBJECTS, NO JSON "
                "ARRAYS. The output must be valid JSON.\n"
                "If you cannot find any mention of something in the text, "
                'please respond with "None found" as the description for '
                "that category.\n"
                "For each character in the chapter, describe their "
                "appearance, personality, mood, and relationships to other "
                "characters\n"
                "An example from an early chapter of Jane Eyre:\n"
                '"Jane Eyre": {"Appearance": "Average height, slender build, '
                "fair skin, dark brown hair, hazel eyes, plain "
                'appearance", "Personality": "Reserved, self-reliant, '
                'modest", "Mood": "Angry at her aunt about her treatment '
                'while at Gateshead"}\n'
                "For each setting in the chapter, note how the setting is "
                "described, where it is in relation to other locations "
                "and whether the characters appear to be familiar or "
                "unfamiliar with the location. Be detailed but concise.\n"
                "If you are unsure of a setting or no setting is shown in "
                'the text, please respond with "None found" as the '
                "description for that setting.\n"
                "Here is an example from Wuthering Heights:\n"
                '"Moors": {"Appearance": Expansive, desolate, rugged, with '
                'high winds and craggy rocks", "Relative location": "Surrounds '
                'Wuthering Heights estate", "Main character\'s familiarity": '
                '"Very familiar, Catherine spent significant time roaming '
                'here as a child and represents freedom to her"}\n'
                '{"Characters": {"Appearance": "Description", "Personality": '
                '"Description", "Mood": "Description", "Relationships with '
                'other characters": "Description", "Thoughts": "Description", '
                '"Actions": "Description"}}{"Settings": {"Appearance": '
                '"Description", "Relative location": "Description", '
                '"Familiarity for main character": "Description"}}'
            ),
            max_tokens=400,
        )
    ]


def test_name_analyzer_analyze_names(name_analyzer, mock_ai_interface):
    mock_ai_interface.call_api.return_value = '{"Characters": {"Character1": {"Appearance": "Test Appearance", "Personality": "Test Personality", "Mood": "Test Mood", "Relationships with other characters": "Test Relationships", "Thoughts": "Test Thoughts", "Actions": "Test Actions"}}, "Settings": {"Setting1": {"Appearance": "Test Appearance", "Relative location": "Test Relative location", "Familiarity for main character": "Test Familiarity for main character"}}}'
    analysis = name_analyzer.analyze_names()
    mock_ai_interface.set_model.assert_called_once_with(
        name_analyzer._ai_config, 1
    )
    mock_ai_interface.create_payload.assert_called_once_with(
        f"Text: {name_analyzer.chapter.text}",
        name_analyzer._role_scripts[0].script,
        name_analyzer._role_scripts[0].max_tokens,
    )
    mock_ai_interface.call_api.assert_called_once_with(
        {
            "model_name": "Mock Model",
            "prompt": f"Text: {name_analyzer.chapter.text}",
            "temperature": 1.0,
            "role_script": name_analyzer._role_scripts[0].script,
            "max_tokens": 400,
        },
        True,
    )
    assert analysis == {
        "Characters": {
            "Character1": {
                "Appearance": "Test Appearance",
                "Personality": "Test Personality",
                "Mood": "Test Mood",
                "Relationships with other characters": "Test Relationships",
                "Thoughts": "Test Thoughts",
                "Actions": "Test Actions",
            }
        },
        "Settings": {
            "Setting1": {
                "Appearance": "Test Appearance",
                "Relative location": "Test Relative location",
                "Familiarity for main character": "Test Familiarity for main character",
            }
        },
    }


def test_name_analyzer_parse_response(name_analyzer):
    response = '{"Characters": {"Character1": {"Appearance": "Test Appearance", "Personality": "Test Personality", "Mood": "Test Mood", "Relationships with other characters": "Test Relationships", "Thoughts": "Test Thoughts", "Actions": "Test Actions"}}, "Settings": {"Setting1": {"Appearance": "Test Appearance", "Relative location": "Test Relative location", "Familiarity for main character": "Test Familiarity for main character"}}}'
    analysis = name_analyzer._parse_response(response)
    assert analysis == {
        "Characters": {
            "Character1": {
                "Appearance": "Test Appearance",
                "Personality": "Test Personality",
                "Mood": "Test Mood",
                "Relationships with other characters": "Test Relationships",
                "Thoughts": "Test Thoughts",
                "Actions": "Test Actions",
            }
        },
        "Settings": {
            "Setting1": {
                "Appearance": "Test Appearance",
                "Relative location": "Test Relative location",
                "Familiarity for main character": "Test Familiarity for main character",
            }
        },
    }


def test_name_summarizer_init(name_summarizer, mock_ai_models):
    assert name_summarizer._ai_config.provider == "mock_provider"
    assert name_summarizer.temperature == 0.4
    assert name_summarizer.max_tokens == 200


def test_name_summarizer_build_role_script(name_summarizer):
    name_summarizer.build_role_script()
    assert name_summarizer._single_role_script.script == (
        "You are an expert summarizer. Please summarize the description "
        "over the course of the story for the following:"
    )
    assert name_summarizer._single_role_script.max_tokens == 200


def test_name_summarizer_create_prompts_characters(name_summarizer):
    name_summarizer.lorebinder = {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
            }
        }
    }
    prompts = list(name_summarizer._create_prompts())
    assert prompts == [
        (
            "Characters",
            "Character1",
            "Character1: Thoughts: Thinking, Thoughts: Thinking, Thoughts: Thinking",
        )
    ]


def test_name_summarizer_create_prompts_settings(name_summarizer):
    name_summarizer.lorebinder = {
        "Settings": {
            "Setting1": {
                "1": {"Appearance": "Test Appearance"},
                "2": {"Appearance": "Test Appearance"},
                "3": {"Appearance": "Test Appearance"},
            }
        }
    }
    prompts = list(name_summarizer._create_prompts())
    assert prompts == [
        (
            "Settings",
            "Setting1",
            "Setting1: Appearance: Test Appearance, Appearance: Test Appearance, Appearance: Test Appearance",
        )
    ]


def test_name_summarizer_create_prompts_other(name_summarizer):
    name_summarizer.lorebinder = {
        "Events": {
            "Event1": ["Event 1", "Event 2", "Event 3"],
            "Event2": ["Event 1", "Event 2", "Event 3"],
            "Event3": ["Event 1", "Event 2", "Event 3"],
        }
    }
    prompts = list(name_summarizer._create_prompts())
    assert prompts == [
        ("Events", "Event1", "Event1: Event 1, Event 2, Event 3"),
        ("Events", "Event2", "Event2: Event 1, Event 2, Event 3"),
        ("Events", "Event3", "Event3: Event 1, Event 2, Event 3"),
    ]


def test_name_summarizer_create_prompts_minimum_chapter_threshold(
    name_summarizer,
):
    name_summarizer.lorebinder = {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
            }
        }
    }
    prompts = list(name_summarizer._create_prompts())
    assert prompts == []


def test_name_summarizer_summarize_names(name_summarizer, mock_ai_interface):
    name_summarizer.lorebinder = {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
            }
        }
    }
    mock_ai_interface.call_api.return_value = "Test Summary"
    name_summarizer._current_category = "Characters"
    name_summarizer._current_name = "Character1"
    lorebinder = name_summarizer.summarize_names(name_summarizer.lorebinder)
    mock_ai_interface.set_model.assert_called_once_with(
        name_summarizer._ai_config, 1
    )
    mock_ai_interface.create_payload.assert_called_once_with(
        "Character1: Thoughts: Thinking, Thoughts: Thinking, Thoughts: Thinking",
        name_summarizer._single_role_script.script,
        name_summarizer._single_role_script.max_tokens,
    )
    mock_ai_interface.call_api.assert_called_once_with(
        {
            "model_name": "Mock Model",
            "prompt": "Character1: Thoughts: Thinking, Thoughts: Thinking, Thoughts: Thinking",
            "temperature": 1.0,
            "role_script": name_summarizer._single_role_script.script,
            "max_tokens": 200,
        },
        False,
    )
    assert lorebinder == {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
                "summary": "Test Summary",
            }
        }
    }


def test_name_summarizer_parse_response(name_summarizer):
    name_summarizer._current_category = "Characters"
    name_summarizer._current_name = "Character1"
    name_summarizer.lorebinder = {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
            }
        }
    }
    response = "Test Summary"
    lorebinder = name_summarizer._parse_response(response)
    assert lorebinder == {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
                "summary": "Test Summary",
            }
        }
    }


def test_name_summarizer_parse_response_empty_response(name_summarizer):
    name_summarizer._current_category = "Characters"
    name_summarizer._current_name = "Character1"
    name_summarizer.lorebinder = {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
            }
        }
    }
    response = ""
    lorebinder = name_summarizer._parse_response(response)
    assert lorebinder == {
        "Characters": {
            "Character1": {
                "1": {"Thoughts": "Thinking"},
                "2": {"Thoughts": "Thinking"},
                "3": {"Thoughts": "Thinking"},
            }
        }
    }
