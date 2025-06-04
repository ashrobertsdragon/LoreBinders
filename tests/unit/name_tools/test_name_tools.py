import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from lorebinders._types import InstructionType
from lorebinders.name_tools.name_tools import get_instruction_text, get_ai_response


@patch("lorebinders.name_tools.name_tools.Path")
def test_get_instruction_text_no_type(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.read_text.return_value = "test"  
    file_name = "test_file.txt"
    
    result = get_instruction_text(file_name)
    
    assert result == "test"
    mock_path.assert_called_once_with("instructions", "", file_name)
    mock_path_instance.read_text.assert_called_once()


@patch("lorebinders.name_tools.name_tools.Path")
def test_get_instruction_text_with_type(mock_path):
    instruction_type = InstructionType.JSON
    mock_path_instance = mock_path.return_value
    mock_path_instance.read_text.return_value = "test"  
    file_name = "test_file.txt"

    result = get_instruction_text(file_name, instruction_type=instruction_type)
    
    assert result == "test"
    mock_path.assert_called_once_with("instructions", "json", file_name)
    mock_path_instance.read_text.assert_called_once()

def test_get_ai_response():

    ai = Mock()
    role_script = Mock()
    prompt = "test"
    temperature = 0.5
    json_mode = False

    role_script.script = "test script"
    role_script.max_tokens = 50

    mock_payload = {
        "prompt": prompt,
        "role_script": role_script.script,
        "max_tokens": role_script.max_tokens,
        "temperature": temperature,
    }

    ai.create_payload.return_value = mock_payload
    ai.call_api.return_value = "test response"

    result = get_ai_response(ai, role_script, prompt, temperature, json_mode)

    assert result == "test response"
    ai.create_payload.assert_called_once_with(prompt, role_script.script, temperature, role_script.max_tokens)
    ai.call_api.assert_called_once_with(mock_payload, json_mode)
