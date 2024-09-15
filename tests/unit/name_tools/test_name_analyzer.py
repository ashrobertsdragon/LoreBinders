import pytest
from unittest.mock import Mock, patch

from lorebinders._types import InstructionType
from lorebinders.name_tools.name_analyzer import get_tokens_per, generate_json_schema, generate_markdown_schema, generate_schema,initialize_helpers, initialize_instructions, initialize_role_script_helper, create_instructions, create_role_script, calculate_category_tokens, should_create_new_role_script, append_role_script, build_role_scripts, combine_responses, parse_response, analyze_names, Instructions, RoleScriptHelper

# Fixtures
@pytest.fixture
def default_traits():
    return {
        "Characters": [
            "Appearance",
            "Personality",
            "Mood",
            "Relationships with other characters",
        ],
        "Settings": [
            "Appearance",
            "Relative location",
            "Familiarity for main character",
        ],
    }

@pytest.fixture
def Mock_Instructions():
    instructions = Mock()
    instructions.base = "base"
    instructions.characters = "character"
    instructions.settings = "settings"
    return instructions

@pytest.fixture
def mock_helper():
    mock = Mock()
    mock.instructions = "Mocked instructions"
    mock.added_character_traits = ["Trait1", "Trait2"]
    return mock

@pytest.fixture
def MockChapter():
    mock = Mock()
    mock.text = "Some chapter text"
    return mock

# Test cases for get_tokens_per
def test_get_tokens_per():  # sourcery skip: extract-duplicate-method
    json_type = InstructionType("json")
    json_result = get_tokens_per(json_type)
    assert json_result == {
        "Characters": 200,
        "Settings": 150,
        "Other": 100,
    }

    markdown_type = InstructionType("markdown")
    markdown_result = get_tokens_per(markdown_type)
    assert markdown_result == {
        "Characters": 170,
        "Settings": 127,
        "Other": 85,
    }

# Test cases for generate_json_schema
def test_generate_json_schema_with_default_traits(default_traits):
    category = "Characters"
    expected_schema = ""'{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description"}}'""
    result = generate_json_schema(category, None, default_traits)
    assert result == expected_schema

def test_generate_json_schema_with_unknown_category(default_traits):
    category = "UnknownCategory"
    expected_schema = ""'{"UnknownCategory": "Description"}'""
    result = generate_json_schema(category, None, default_traits)
    assert result == expected_schema

def test_generate_json_schema_with_added_traits(default_traits):
    category = "Characters"
    added_traits = ["Custom Trait 1", "Custom Trait 2"]

    result = generate_json_schema(category, added_traits, default_traits)

    assert "Appearance" in result
    assert "Personality" in result
    assert "Mood" in result
    assert "Relationships with other characters" in result
    assert "Custom Trait 1" in result
    assert "Custom Trait 2" in result

def test_generate_json_schema_handles_empty_added_traits_correctly(default_traits):
    category = "Characters"
    added_traits = []

    result = generate_json_schema(category, added_traits, default_traits)

    assert category in result
    assert "Appearance" in result
    assert "Personality" in result
    assert "Mood" in result
    assert "Relationships with other characters" in result

def test_generate_json_schema_valid_input(default_traits):
    category = "Characters"
    added_traits = ["Extra Trait"]

    result = generate_json_schema(category, added_traits, default_traits)

    expected_result = ""'{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description", "Extra Trait": "Description"}}'""
    assert result == expected_result

def test_generate_json_schema_combines_default_and_added_traits_correctly(default_traits):
    category = "Characters"
    added_traits = ["Custom Trait 1", "Custom Trait 2"]

    result = generate_json_schema(category, added_traits, default_traits)

    expected_schema = ""'{"Characters": {"Appearance": "Description", "Personality": "Description", "Mood": "Description", "Relationships with other characters": "Description", "Custom Trait 1": "Description", "Custom Trait 2": "Description"}}'""

    assert result == expected_schema

# Test cases for generate_markdown_schema
def test_generate_markdown_schema_with_default_traits(default_traits):
    category = "Characters"
    expected_schema = (
        "# Characters\n"
        "## Appearance\nDescription\n"
        "## Personality\nDescription\n"
        "## Mood\nDescription\n"
        "## Relationships with other characters\nDescription\n"
    )
    result = generate_markdown_schema(category, None, default_traits)
    assert result == expected_schema

def test_generate_markdown_schema_with_unknown_category(default_traits):
    category = "UnknownCategory"
    expected_schema = (
        "# UnknownCategory\n"
        "Description\n"
    )
    result = generate_markdown_schema(category, None, default_traits)
    assert result == expected_schema

def test_generate_markdown_schema_handles_empty_added_traits(default_traits):
    category = "Characters"
    added_traits = []

    result = generate_markdown_schema(category, added_traits, default_traits)

    assert category in result
    assert "Appearance" in result
    assert "Personality" in result
    assert "Mood" in result
    assert "Relationships with other characters" in result

def test_combines_default_and_added_traits_correctly(default_traits):
    category = "Characters"
    added_traits = ["Custom Trait 1", "Custom Trait 2"]

    result = generate_markdown_schema(category, added_traits, default_traits)

    expected_schema = "# Characters\n## Appearance\nDescription\n## Personality\nDescription\n## Mood\nDescription\n## Relationships with other characters\nDescription\n## Custom Trait 1\nDescription\n## Custom Trait 2\nDescription\n"

    assert result == expected_schema

def test_manage_added_traits_with_special_characters(default_traits):
    category = "Characters"
    added_traits = ["Trait 1", "Trait 2", "Special!@#$%^&*()"]
    expected_schema = "# Characters\n## Appearance\nDescription\n## Personality\nDescription\n## Mood\nDescription\n## Relationships with other characters\nDescription\n## Trait 1\nDescription\n## Trait 2\nDescription\n## Special!@#$%^&*()\nDescription\n"

    result = generate_markdown_schema(category, added_traits, default_traits)

    assert result == expected_schema

def test_processes_categories_with_numeric_names(default_traits):
    category = "123"
    added_traits = ["Trait1", "Trait2"]
    expected_schema = "# 123\n## Trait1\nDescription\n## Trait2\nDescription\n"
    result = generate_markdown_schema(category, added_traits, default_traits)
    assert result == expected_schema

def test_handles_categories_with_special_characters(default_traits):
    category = "Special Category!@#$%"
    added_traits = ["Trait1", "Trait2"]
    expected_schema = "# Special Category!@#$%\n## Trait1\nDescription\n## Trait2\nDescription\n"

    result = generate_markdown_schema(category, added_traits, default_traits)

    assert result == expected_schema

def test_manage_added_traits_with_empty_strings(default_traits):
    category = "Characters"
    added_traits = [""]
    expected_schema = "# Characters\n## Appearance\nDescription\n## Personality\nDescription\n## Mood\nDescription\n## Relationships with other characters\nDescription\n"

    result = generate_markdown_schema(category, added_traits, default_traits)

    assert result == expected_schema

# Test cases for generate_schema

@patch("lorebinders.name_tools.name_analyzer.generate_json_schema")
def test_generate_schema_calls_generate_json_schema(mock_generate_json_schema):
    category = "Characters"
    added_traits = ["Custom Trait 1"]
    instruction_type = InstructionType.JSON

    result = generate_schema(category, added_traits, instruction_type)

    mock_generate_json_schema.assert_called_once()

@patch("lorebinders.name_tools.name_analyzer.generate_markdown_schema")
def test_generate_schema_calls_generate_markdown_schema(mock_generate_markdown_schema):
        category = "Characters"
        added_traits = ["Trait1", "Trait2"]
        instruction_type = InstructionType.MARKDOWN

        generate_schema(category, added_traits, instruction_type)

        mock_generate_markdown_schema.assert_called_once()

@patch("lorebinders.name_tools.name_analyzer.generate_json_schema")
@patch("lorebinders.name_tools.name_analyzer.generate_markdown_schema")
def test_generate_schema_only_calls_one_function(mock_generate_markdown_schema, mock_generate_json_schema):
        category = "Characters"
        added_traits = ["Trait1", "Trait2"]
        instruction_type = InstructionType.MARKDOWN

        generate_schema(category, added_traits, instruction_type)

        mock_generate_markdown_schema.assert_called_once()
        mock_generate_json_schema.assert_not_called()

        mock_generate_markdown_schema.reset_mock()

        instruction_type = InstructionType.JSON
        generate_schema(category, added_traits, instruction_type)
        mock_generate_json_schema.assert_called_once()
        mock_generate_markdown_schema.assert_not_called()

@patch("lorebinders.name_tools.name_analyzer.generate_json_schema")
def test_generate_schema_none_added_traits(mock_generate_json_schema, default_traits):
    category = "Settings"
    added_traits = None
    instruction_type = InstructionType.JSON

    mock_generate_json_schema.return_value = '{"Settings": {"Appearance": "Description", "Relative location": "Description", "Familiarity for main character": "Description"}}'

    result = generate_schema(category, added_traits, instruction_type)

    mock_generate_json_schema.assert_called_once_with(category, added_traits, default_traits)
    assert result == '{"Settings": {"Appearance": "Description", "Relative location": "Description", "Familiarity for main character": "Description"}}'


def test_generate_schema_handles_empty_added_traits_correctly(default_traits):
    with patch("lorebinders.name_tools.name_analyzer.generate_json_schema") as mock_generate_json_schema:

        category = "Characters"
        added_traits = []
        instruction_type = InstructionType.JSON

        generate_schema(category, added_traits, instruction_type)

        mock_generate_json_schema.assert_called_with(category, added_traits, default_traits)

@patch("lorebinders.name_tools.name_analyzer.generate_markdown_schema")
def test_handles_category_not_present_in_default_traits(mock_generate_markdown_schema, default_traits):

    category = "Locations"
    added_traits = ["Climate", "Population"]
    instruction_type = InstructionType.MARKDOWN

    generate_schema(category, added_traits, instruction_type)

    mock_generate_markdown_schema.assert_called_with(category, added_traits, default_traits)

@patch("lorebinders.name_tools.name_analyzer.generate_markdown_schema")
def test_special_characters_in_category_and_traits(mock_generate_markdown_schema, default_traits):
    category = "Characters!@#$%"
    added_traits = ["Trait 1!@#$%", "Trait 2!@#$%"]
    instruction_type = InstructionType.MARKDOWN

    generate_schema(category, added_traits, instruction_type)

    mock_generate_markdown_schema.assert_called_once_with(category, added_traits, default_traits)

# Test cases for initializing dataclasses
@patch("lorebinders.name_tools.name_analyzer.name_tools.get_instruction_text")
@patch("lorebinders.name_tools.name_analyzer.Instructions")
def test_initialize_instructions_calls_get_instruction_text(MockInstructions, mock_get_instruction_text):

    mock_get_instruction_text.return_value = "test"
    instruction_type = InstructionType.JSON

    initialize_instructions(instruction_type)

    assert mock_get_instruction_text.call_count == 3
    MockInstructions.assert_called_once_with(base="test", characters="test", settings="test")

@patch("lorebinders.name_tools.name_analyzer.RoleScriptHelper")
def test_initialize_roles_script_helper(MockRoleScriptHelper):
    instruction_type = InstructionType.JSON
    absolute_max_tokens = 100
    instructions = Mock()
    added_character_traits = ["test"]

    initialize_role_script_helper(
        instruction_type, absolute_max_tokens, instructions, added_character_traits
    )

    MockRoleScriptHelper.assert_called_once_with(
        instruction_type=instruction_type,
        absolute_max_tokens=absolute_max_tokens,
        instructions=instructions,
        added_character_traits=added_character_traits,
    )

@patch("lorebinders.name_tools.name_analyzer.Instructions")
@patch("lorebinders.name_tools.name_analyzer.RoleScriptHelper")
@patch("lorebinders.name_tools.name_analyzer.initialize_instructions")
def test_initialize_helpers_calls_get_instruction_text(mock_initialize_instructions, MockRoleScriptHelper, MockInstructions):
    instruction_type = InstructionType.JSON
    absolute_max_tokens = 100
    added_character_traits = ["test"]
    mock_initialize_instructions.return_value = MockInstructions
    initialize_helpers(instruction_type, absolute_max_tokens, added_character_traits)

    mock_initialize_instructions.assert_called_once()
    MockRoleScriptHelper.assert_called_once_with(
        instruction_type=instruction_type,
        absolute_max_tokens=absolute_max_tokens,
        instructions=MockInstructions,
        added_character_traits=added_character_traits,
    )

# Test cases for create_instructions
def test_create_instructions_base_categories(Mock_Instructions):
    categories = ["Characters", "Settings"]

    result = create_instructions(categories, Mock_Instructions)

    assert result == 'base\ncharacter\nsettings\nYou will format this information using the following schema where "description" is replaced with the actual information.\n'

def test_create_instructions_base_and_single_other_category(Mock_Instructions):
    categories = ["Characters", "Sports"]

    result = create_instructions(categories, Mock_Instructions)

    assert result == 'base\ncharacter\nProvide descriptions of Sports without referencing specific characters or plot points.\nYou will format this information using the following schema where "description" is replaced with the actual information.\n'

def test_create_instructions_base_and_multiple_other_category(Mock_Instructions):
    categories = ["Characters", "Sports", "Art"]

    result = create_instructions(categories, Mock_Instructions)
    expected = (
        "base\n"
        "character\n"
        "Provide descriptions of Sports, Art without referencing specific characters or plot points.\n"
        'You will format this information using the following schema where "description" is replaced with the actual information.\n'
    )

    assert result == expected

def test_create_instructions_no_base_multiple_other_category(Mock_Instructions):
    categories = ["Sports", "Art"]

    result = create_instructions(categories, Mock_Instructions)
    expected = (
        "base\n"
        "Provide descriptions of Sports, Art without referencing specific characters or plot points.\n"
        'You will format this information using the following schema where "description" is replaced with the actual information.\n'
    )
    assert result == expected

# Test cases for create_role_script
@patch("lorebinders.name_tools.name_analyzer.create_instructions")
@patch("lorebinders.name_tools.name_analyzer.generate_schema")
@patch("lorebinders.name_tools.name_analyzer.RoleScript")
def test_create_role_script_single_category(
    mock_role_script, mock_generate_schema, mock_create_instructions, mock_helper
):
    categories = ["Category1"]
    max_tokens = 100
    instruction_type = InstructionType.JSON
    mock_create_instructions.return_value = "Mocked instruction text"
    mock_generate_schema.return_value = "Mocked schema text"

    create_role_script(categories, max_tokens, mock_helper, instruction_type)

    mock_create_instructions.assert_called_once_with(categories, "Mocked instructions")
    mock_generate_schema.assert_called_once_with("Category1", ["Trait1", "Trait2"], instruction_type)
    mock_role_script.assert_called_once_with("Mocked instruction textMocked schema text", max_tokens)



@patch("lorebinders.name_tools.name_analyzer.create_instructions")
@patch("lorebinders.name_tools.name_analyzer.generate_schema")
@patch("lorebinders.name_tools.name_analyzer.RoleScript")
def test_create_role_script_multiple_categories(
    mock_role_script, mock_generate_schema, mock_create_instructions, mock_helper
):

    categories = ["Category1", "Category2", "Category3"]
    max_tokens = 200
    instruction_type = InstructionType.MARKDOWN
    mock_create_instructions.return_value = "Mocked instruction text"
    mock_generate_schema.side_effect = [
        "Mocked schema text 1",
        "Mocked schema text 2",
        "Mocked schema text 3",
    ]

    create_role_script(categories, max_tokens, mock_helper, instruction_type)

    mock_create_instructions.assert_called_once_with(categories, "Mocked instructions")
    assert mock_generate_schema.call_count == 3
    mock_generate_schema.assert_any_call("Category1", ["Trait1", "Trait2"], instruction_type)
    mock_generate_schema.assert_any_call("Category2", ["Trait1", "Trait2"], instruction_type)
    mock_generate_schema.assert_any_call("Category3", ["Trait1", "Trait2"], instruction_type)
    mock_role_script.assert_called_once_with(
        "Mocked instruction textMocked schema text 1Mocked schema text 2Mocked schema text 3", max_tokens
    )

@patch("lorebinders.name_tools.name_analyzer.create_instructions")
@patch("lorebinders.name_tools.name_analyzer.generate_schema")
@patch("lorebinders.name_tools.name_analyzer.RoleScript")
def test_create_role_script_empty_categories(
    mock_role_script, mock_generate_schema, mock_create_instructions, mock_helper
):

    categories = []
    max_tokens = 100
    instruction_type = InstructionType.JSON
    mock_create_instructions.return_value = "Mocked instruction text"

    create_role_script(categories, max_tokens, mock_helper, instruction_type)

    mock_create_instructions.assert_called_once_with(categories, "Mocked instructions")
    mock_generate_schema.assert_not_called()
    mock_role_script.assert_called_once_with("Mocked instruction text", max_tokens)

@patch("lorebinders.name_tools.name_analyzer.create_instructions")
@patch("lorebinders.name_tools.name_analyzer.generate_schema")
@patch("lorebinders.name_tools.name_analyzer.RoleScript")
def test_create_role_script_no_added_traits(
    mock_role_script, mock_generate_schema, mock_create_instructions, mock_helper
):

    categories = ["Category1"]
    max_tokens = 100
    instruction_type = InstructionType.JSON
    mock_helper.added_character_traits = []
    mock_create_instructions.return_value = "Mocked instruction text"
    mock_generate_schema.return_value = "Mocked schema text"


    create_role_script(categories, max_tokens, mock_helper, instruction_type)

    mock_create_instructions.assert_called_once_with(categories, "Mocked instructions")
    mock_generate_schema.assert_called_once_with("Category1", [], instruction_type)
    mock_role_script.assert_called_once_with("Mocked instruction textMocked schema text", max_tokens)

@patch("lorebinders.name_tools.name_analyzer.create_instructions")
@patch("lorebinders.name_tools.name_analyzer.generate_schema")
@patch("lorebinders.name_tools.name_analyzer.RoleScript")
def test_create_role_script_special_characters(
    mock_role_script, mock_generate_schema, mock_create_instructions, mock_helper
):

    categories = ["Cat@egory1!", "Cat#egory2$"]
    max_tokens = 100
    instruction_type = InstructionType.MARKDOWN
    mock_create_instructions.return_value = "Mocked instruction text"
    mock_generate_schema.side_effect = [
        "Mocked schema text 1",
        "Mocked schema text 2",
    ]

    create_role_script(categories, max_tokens, mock_helper, instruction_type)

    mock_create_instructions.assert_called_once_with(categories, "Mocked instructions")
    assert mock_generate_schema.call_count == 2
    mock_generate_schema.assert_any_call("Cat@egory1!", ["Trait1", "Trait2"], instruction_type)
    mock_generate_schema.assert_any_call("Cat#egory2$", ["Trait1", "Trait2"], instruction_type)
    mock_role_script.assert_called_once_with(
        "Mocked instruction textMocked schema text 1Mocked schema text 2", max_tokens
    )

# Test build_role_scripts helper functions
@pytest.mark.parametrize(
    "names, instruction_type, category, max_tokens, expected",
    [
        (["Alice"], InstructionType.JSON, "Category1", 50, 10),
        (["Alice", "Bob"], InstructionType.JSON, "Category1", 50, 20),
        (["Alice", "Bob", "Charlie"], InstructionType.JSON, "Category1", 20, 20),
        (["Alice", "Bob", "Charlie", "Dave"], InstructionType.JSON, "Category1", 50, 40),
        (["Alice"], InstructionType.JSON, "Other", 50, 5),
        (["Alice", "Bob"], InstructionType.JSON, "Other", 50, 10),
        (["Alice", "Bob", "Charlie"], InstructionType.JSON, "Other", 15, 15),
        (["Alice", "Bob", "Charlie", "Dave"], InstructionType.JSON, "Other", 10, 10),
    ]
)
@patch("lorebinders.name_tools.name_analyzer.get_tokens_per")
def test_calculate_category_tokens(
    mock_get_tokens_per, names, instruction_type, category, max_tokens, expected
):
    mock_get_tokens_per.return_value = {"Category1": 10, "Other": 5}
    result = calculate_category_tokens(names, instruction_type, category, max_tokens)
    assert result == expected
    mock_get_tokens_per.assert_called_once_with(instruction_type)

@pytest.mark.parametrize(
    "current_tokens, category_tokens, max_tokens, expected",
    [
        (50, 30, 70, True),  # current_tokens + category_tokens = 80 > max_tokens
        (20, 40, 70, False), # current_tokens + category_tokens = 60 <= max_tokens
        (60, 20, 80, False), # current_tokens + category_tokens = 80 = max_tokens
        (90, 10, 100, False),# current_tokens + category_tokens = 100 = max_tokens
        (25, 55, 70, True),  # current_tokens + category_tokens = 80 > max_tokens
        (0, 70, 70, False),  # current_tokens + category_tokens = 70 = max_tokens
        (100, 1, 100, True), # current_tokens + category_tokens = 101 > max_tokens
        (30, 40, 70, False), # current_tokens + category_tokens = 70 = max_tokens
    ]
)
def test_should_create_new_role_script(current_tokens, category_tokens, max_tokens, expected):
    result = should_create_new_role_script(current_tokens, category_tokens, max_tokens)

    assert result == expected

# Test cases for append_role_script
@patch("lorebinders.name_tools.name_analyzer.create_role_script")
def test_append_role_script_empty_list(mock_create_role_script, mock_helper):
    role_scripts = []
    current_categories = ["Category1"]
    current_tokens = 100
    instruction_type = InstructionType.JSON
    mock_role_script = Mock()
    mock_create_role_script.return_value = mock_role_script

    result = append_role_script(role_scripts, current_categories, current_tokens, mock_helper, instruction_type)

    mock_create_role_script.assert_called_once_with(current_categories, current_tokens, mock_helper, instruction_type)
    assert result == [mock_role_script]
    assert result is role_scripts

@patch("lorebinders.name_tools.name_analyzer.create_role_script")
def test_append_role_script_existing_list(mock_create_role_script, mock_helper):

    current_categories = ["Category1"]
    current_tokens = 100
    instruction_type = InstructionType.JSON
    mock_role_script = Mock()
    mock_create_role_script.return_value = mock_role_script
    role_scripts = [mock_role_script]

    result = append_role_script(role_scripts, current_categories, current_tokens, mock_helper, instruction_type)

    mock_create_role_script.assert_called_once_with(current_categories, current_tokens, mock_helper, instruction_type)
    assert len(result) == 2
    assert result is role_scripts

# Test cases for build_role_scripts
@patch("lorebinders.name_tools.name_analyzer.calculate_category_tokens")
@patch("lorebinders.name_tools.name_analyzer.should_create_new_role_script")
@patch("lorebinders.name_tools.name_analyzer.append_role_script")
def test_empty_chapter_data(mock_append, mock_should_create, mock_calculate, mock_helper):
    result = build_role_scripts({}, mock_helper, InstructionType.JSON)
    assert result == []
    mock_calculate.assert_not_called()
    mock_should_create.assert_not_called()
    mock_append.assert_not_called()

@patch("lorebinders.name_tools.name_analyzer.calculate_category_tokens")
@patch("lorebinders.name_tools.name_analyzer.should_create_new_role_script")
@patch("lorebinders.name_tools.name_analyzer.append_role_script")
def test_single_category(mock_append, mock_should_create, mock_calculate, mock_helper):
    mock_calculate.return_value = 100
    mock_should_create.return_value = False
    mock_append.return_value = [Mock()]

    chapter_data = {"category1": ["name1", "name2"]}
    result = build_role_scripts(chapter_data, mock_helper, InstructionType.JSON)

    assert len(result) == 1
    mock_calculate.assert_called_once_with(
        ["name1", "name2"],
        mock_helper.instruction_type,
        "category1",
        mock_helper.absolute_max_tokens,
    )
    mock_should_create.assert_called_once()
    mock_append.assert_called_once()

@patch("lorebinders.name_tools.name_analyzer.calculate_category_tokens")
@patch("lorebinders.name_tools.name_analyzer.should_create_new_role_script")
@patch("lorebinders.name_tools.name_analyzer.append_role_script")
def test_multiple_categories_single_script(mock_append, mock_should_create, mock_calculate, mock_helper):
    mock_calculate.return_value = 100
    mock_should_create.return_value = False
    mock_append.return_value = [Mock()]

    chapter_data = {
        "category1": ["name1", "name2"],
        "category2": ["name3", "name4"],
    }
    result = build_role_scripts(chapter_data, mock_helper, InstructionType.JSON)

    assert len(result) == 1
    assert mock_calculate.call_count == 2
    assert mock_should_create.call_count == 2
    mock_append.assert_called_once()

@patch("lorebinders.name_tools.name_analyzer.calculate_category_tokens")
@patch("lorebinders.name_tools.name_analyzer.should_create_new_role_script")
@patch("lorebinders.name_tools.name_analyzer.append_role_script")
def test_multiple_categories_multiple_scripts(mock_append, mock_should_create, mock_calculate, mock_helper):
    MockRoleScript = Mock()
    mock_calculate.side_effect = [100, 200, 300]
    mock_should_create.side_effect = [False, True, False]
    mock_append.side_effect = [[MockRoleScript], [MockRoleScript, MockRoleScript]]

    chapter_data = {
        "category1": ["name1", "name2"],
        "category2": ["name3", "name4", "name5"],
        "category3": ["name6", "name7", "name8", "name9"],
    }

    result = build_role_scripts(chapter_data, mock_helper, InstructionType.JSON)

    assert len(result) == 2
    assert mock_calculate.call_count == 3
    assert mock_should_create.call_count == 3
    assert mock_append.call_count == 2

# Test cases for combine_responses
def test_combine_responses_single_value_json_mode():
    responses = ['{"key": "value"}']
    result = combine_responses(responses, json_mode=True)
    assert result == '{"key": "value"}'

def test_combine_responses_two_values_json_mode():
    responses = ['{"key1": "value1"}', '{"key2": "value2"}']
    result = combine_responses(responses, json_mode=True)
    assert result == '{"key1": "value1","key2": "value2"}'

def test_combine_responses_three_values_json_mode():
    responses = ['{"key1": "value1"}', '{"key2": "value2"}', '{"key3": "value3"}']
    result = combine_responses(responses, json_mode=True)
    assert result == '{"key1": "value1","key2": "value2","key3": "value3"}'

def test_combine_responses_single_value_non_json_mode():
    responses = ["value"]
    result = combine_responses(responses, json_mode=False)
    assert result == "value"

def test_combine_responses_two_values_non_json_mode():
    responses = ["value1", "value2"]
    result = combine_responses(responses, json_mode=False)
    assert result == "value1\nvalue2"

def test_combine_responses_three_values_non_json_mode():
    responses = ["value1", "value2", "value3"]
    result = combine_responses(responses, json_mode=False)
    assert result == "value1\nvalue2\nvalue3"

# Test cases for parse_response
@patch("lorebinders.json_tools.json_str_to_dict")
@patch("lorebinders.markdown_parser.markdown_to_dict")
def test_parse_response_json_mode(mock_markdown_to_dict, mock_json_str_to_dict):
    mock_json_str_to_dict.return_value = {"key": "value"}
    response = '{"key": "value"}'
    json_mode = True

    result = parse_response(response, json_mode)

    mock_json_str_to_dict.assert_called_once_with(response)
    assert result == {"key": "value"}
    mock_markdown_to_dict.assert_not_called()

@patch("lorebinders.json_tools.json_str_to_dict")
@patch("lorebinders.markdown_parser.markdown_to_dict")
def test_parse_response_non_json_mode(mock_markdown_to_dict, mock_json_str_to_dict):
    mock_markdown_to_dict.return_value = {"key": "value"}
    response = "key: value"
    json_mode = False

    result = parse_response(response, json_mode)

    mock_markdown_to_dict.assert_called_once_with(response)
    assert result == {"key": "value"}
    mock_json_str_to_dict.assert_not_called()

# Test cases for analyze_names
@patch("lorebinders.name_tools.name_analyzer.name_tools.get_ai_response")
@patch("lorebinders.name_tools.name_analyzer.combine_responses")
@patch("lorebinders.name_tools.name_analyzer.parse_response")
def test_analyze_names_json_mode(mock_parse_response, mock_combine_responses, mock_get_ai_response, MockChapter):
    ai = "AIInterface"
    RoleScript = "RoleScript"
    instruction_type = InstructionType.JSON
    role_scripts = [RoleScript, RoleScript]

    mock_get_ai_response.side_effect = ["response1", "response2"]
    mock_combine_responses.return_value = "combined_response"
    mock_parse_response.return_value = {"parsed_key": "parsed_value"}

    result = analyze_names(ai, instruction_type, role_scripts, MockChapter)

    assert mock_get_ai_response.call_count == len(role_scripts)
    mock_get_ai_response.assert_called_with(ai=ai, role_script=RoleScript, prompt="Text: Some chapter text", temperature=0.4, json_mode=True)
    mock_combine_responses.assert_called_once_with(responses=["response1", "response2"], json_mode=True)
    mock_parse_response.assert_called_once_with(response="combined_response", json_mode=True)
    assert result == {"parsed_key": "parsed_value"}

@patch("lorebinders.name_tools.name_analyzer.name_tools.get_ai_response")
@patch("lorebinders.name_tools.name_analyzer.combine_responses")
@patch("lorebinders.name_tools.name_analyzer.parse_response")
def test_analyze_names_markdown_mode(mock_parse_response, mock_combine_responses, mock_get_ai_response, MockChapter):
    ai = "AIInterface"
    RoleScript = "RoleScript"
    instruction_type = InstructionType.MARKDOWN
    role_scripts = [RoleScript, RoleScript, RoleScript]

    mock_get_ai_response.side_effect = ["response1", "response2", "response3"]
    mock_combine_responses.return_value = "combined_response"
    mock_parse_response.return_value = {"parsed_key": "parsed_value"}

    result = analyze_names(ai, instruction_type, role_scripts, MockChapter)

    assert mock_get_ai_response.call_count == len(role_scripts)
    mock_get_ai_response.assert_called_with(ai=ai, role_script=RoleScript, prompt="Text: Some chapter text", temperature=0.4, json_mode=False)
    mock_combine_responses.assert_called_once_with(responses=["response1", "response2", "response3"], json_mode=False)
    mock_parse_response.assert_called_once_with(response="combined_response", json_mode=False)
    assert result == {"parsed_key": "parsed_value"}
