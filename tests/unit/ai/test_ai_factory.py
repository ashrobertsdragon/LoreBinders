import pytest

import re
from unittest.mock import Mock, patch

from pydantic import ValidationError

from lorebinders.ai.ai_factory import AIManager, Payload

@pytest.fixture
def mock_ai_manager():
    class TestManager(AIManager):
        def __init__(self, email_handler) -> None:
            self.unresolvable_errors = self._set_unresolvable_errors()
            self.error_handler = Mock()
            self.api_model: str | None = None
        def _set_unresolvable_errors(self) -> tuple:
            return ("a", "b")
        def _count_tokens(self, text) -> int:
            return 1
        def create_message_payload(self, role_script, prompt, assistant_message = None) -> tuple[list, int]:
            return[role_script, prompt, assistant_message], 0
        def call_api(self, api_payload, json_response = False, retry_count = 0, assistant_message = None) -> str:
            return ""
        def preprocess_response(self, response):
            return response
        def process_response(self,content_tuple, api_payload, retry_count, json_response,assistant_message = None) -> str:
            return ""

    return TestManager("email_handler")

@patch("lorebinders.ai.ai_factory.Payload")
def test_create_payload(MockPayload, mock_ai_manager):

    mock_ai_manager.api_model = "mock_model"
    prompt = "test prompt"
    role_script = "test script"
    temperature = 0.5
    max_tokens = 100

    test_payload = {
        "api_model": "mock_model",
        "role_script": "test script",
        "prompt": "test prompt",
        "temperature": 0.5,
        "max_tokens": 100
    }
    mock_payload = Mock()
    mock_payload.model_dump.return_value = test_payload
    MockPayload.return_value = mock_payload

    result = mock_ai_manager.create_payload(prompt, role_script, temperature, max_tokens)

    MockPayload.assert_called_once_with(
        api_model="mock_model",
        role_script=role_script,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens

    )
    assert result == test_payload

@patch("lorebinders.ai.ai_factory.Payload")
def test_create_payload_api_model_not_set(MockPayload, mock_ai_manager):
    prompt = "test prompt"
    role_script = "test script"
    temperature = 0.5
    max_tokens = 100

    with pytest.raises(AttributeError, match=re.escape("AI model not set. Call set_model() first.")):
        mock_ai_manager.create_payload(prompt, role_script, temperature, max_tokens)

    MockPayload.assert_not_called()

# Test using real Payload class
@patch("lorebinders.ai.ai_factory.logger")
def test_create_payload_logs_payload_validation_error(mock_logger, mock_ai_manager):

    mock_ai_manager.api_model = "mock_model"
    prompt = None
    role_script = "test script"
    temperature = 0.5
    max_tokens = 100

    with pytest.raises(ValidationError):

        result= mock_ai_manager.create_payload(prompt, role_script, temperature, max_tokens)
        print(result)
    mock_logger.exception.assert_called_once_with('1 validation error for Payload\nprompt\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.6/v/string_type')

def test_modify_payload(mock_ai_manager):

    mock_ai_manager.api_model = "mock_model"
    new_prompt = "test prompt 2"

    test_payload = {
        "api_model": "mock_model",
        "role_script": "test script",
        "prompt": "test prompt",
        "temperature": 0.5,
        "max_tokens": 100
    }
    result = mock_ai_manager.modify_payload(test_payload, prompt=new_prompt)

    assert result == test_payload

@patch("lorebinders.ai.ai_factory.RateLimit")
def test_set_model(MockRateLimit, mock_ai_manager):
    mock_model = Mock()
    mock_model.name = "mock_model"
    mock_model.api_model = "mock-model"
    mock_model.rate_limit = 1000

    mock_rate_handler = Mock()
    mock_rate_limit = Mock()
    MockRateLimit.return_value = mock_rate_limit
    mock_ai_manager.set_model(mock_model, mock_rate_handler)

    assert mock_ai_manager.model == mock_model
    assert mock_ai_manager.api_model == mock_model.api_model
    assert mock_ai_manager.rate_limiter == mock_rate_limit
    MockRateLimit.assert_called_once_with(mock_model.name, mock_ai_manager.model.rate_limit, mock_rate_handler)

@pytest.fixture(params=[
    (10, 100, False, 'assert_not_called'),
    (50, 100, False, 'assert_not_called'),
    (100, 100, False, 'assert_not_called'),
    (101, 100, True, 'assert_called_once'),
    (200, 100, True, 'assert_called_once'),
])
def rate_limit_params(request):
    return request.param

def test_enforce_rate_limit(mock_ai_manager,  rate_limit_params):
    input_tokens, max_tokens, is_exceeded, cool_down_assertion = rate_limit_params
    mock_ai_manager.rate_limiter = Mock()
    mock_ai_manager.rate_limiter.is_rate_limit_exceeded = Mock(return_value=is_exceeded)
    mock_ai_manager.rate_limiter.cool_down = Mock()
    mock_ai_manager._enforce_rate_limit(input_tokens, max_tokens)

    mock_ai_manager.rate_limiter.is_rate_limit_exceeded.assert_called_once_with(input_tokens, max_tokens)

    getattr(mock_ai_manager.rate_limiter.cool_down, cool_down_assertion)()

def test_error_handle(mock_ai_manager):
    mock_ai_manager.error_handler = Mock()
    mock_ai_manager.error_handler.handle_error = Mock()
    mock_ai_manager.error_handler.handle_error.return_value = 1
    mock_exception = Exception("test exception")

    result = mock_ai_manager._error_handle(mock_exception, 0)

    assert result == 1
    mock_ai_manager.error_handler.handle_error.assert_called_once_with(mock_exception, 0)

def test_update_rate_limit_dict(mock_ai_manager):
    mock_ai_manager.rate_limiter = Mock()
    mock_ai_manager.rate_limiter.update_rate_limit_dict = Mock()
    mock_ai_manager.rate_limiter.rate_limit_dict = {"tokens_used": 20}

    mock_ai_manager._update_rate_limit_dict(20)

    mock_ai_manager.rate_limiter.update_rate_limit_dict.assert_called_once()
    assert mock_ai_manager.rate_limiter.rate_limit_dict == {"tokens_used": 40}
