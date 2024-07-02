import time
import pytest
from unittest.mock import patch, MagicMock
from lorebinders.ai.ai_factory import RateLimit, AIFactory
from lorebinders._managers import EmailManager, RateLimitManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.attributes import RoleScript
from lorebinders.ai.exceptions import MaxRetryError

@pytest.fixture
def mock_rate_limit_manager():
    return MagicMock(spec=RateLimitManager)

@pytest.fixture
def mock_email_manager():
    return MagicMock(spec=EmailManager)

@pytest.fixture
def model_name():
    return "test_model"

@pytest.fixture
def rate_limit_value():
    return 7000

@pytest.fixture
def rate_limit(model_name, rate_limit_value, mock_rate_limit_manager):
    return RateLimit(model_name, rate_limit_value, mock_rate_limit_manager)

@pytest.fixture
def ai_factory(mock_email_manager, mock_rate_limit_manager, model_name):
    factory = AIFactory()
    factory.model_name = model_name
    factory.rate_limiter = RateLimit(model_name, rate_limit_value, mock_rate_limit_manager)
    factory.error_handler = APIErrorHandler(
        email_manager=mock_email_manager,
        unresolvable_errors=(Exception,)  # Replace with actual unresolvable errors
    )
    return factory

@pytest.fixture
def role_script():
    return RoleScript(script="Test role script", max_tokens=50)

@pytest.fixture
def payload_data():
    return {
        "model_name": "test_model",
        "role_script": "test_script",
        "prompt": "test_prompt",
        "temperature": 1.0,
        "max_tokens": 100
    }

@pytest.fixture
def mock_payload():
    return MagicMock(
        model_dump=lambda: {
            "model_name": "test_model",
            "role_script": "test_script",
            "prompt": "test_prompt",
            "temperature": 1.0,
            "max_tokens": 100
        }
    )

class ConcreteAIFactory(AIFactory):
    def _count_tokens(self, text: str) -> int:
        return len(text)

    def create_message_payload(self, role_script: str, prompt: str, assistant_message: str | None = None) -> tuple[list, int]:
        return [], 0

    def call_api(self, api_payload: dict, json_response: bool = False, retry_count: int = 0, assistant_message: str | None = None) -> str:
        return "API response"

    def preprocess_response(self, response: str) -> tuple[str, int, str]:
        return "Content", 10, "stop"

    def process_response(self, content_tuple: tuple[str, int, str], api_payload: dict, retry_count: int, json_response: bool, assistant_message: str | None = None) -> str:
        return "Processed response"

    def _set_unresolvable_errors(self) -> tuple:
        return (Exception,)

@pytest.fixture
def mock_rate_limit_manager():
    manager = MagicMock()
    manager.read.return_value = {"minute": 1000, "tokens_used": 0}
    return manager

@pytest.fixture
def rate_limit(model_name, rate_limit_value, mock_rate_limit_manager):
    return RateLimit(model_name, rate_limit_value, mock_rate_limit_manager)

@pytest.fixture
def ai_factory(mock_email_manager, mock_rate_limit_manager, model_name, rate_limit_value):
    factory = ConcreteAIFactory()
    factory.set_model(MagicMock(name=model_name, rate_limit=rate_limit_value), mock_rate_limit_manager)
    factory.error_handler.email_manager = mock_email_manager
    return factory

def test_rate_limit_reset_rate_limit_dict(rate_limit, mock_rate_limit_manager, model_name):
    with patch('time.time', return_value=2000):
        rate_limit.reset_rate_limit_dict()
        assert rate_limit.rate_limit_dict["minute"] == 2000
        assert rate_limit.rate_limit_dict["tokens_used"] == 0
        mock_rate_limit_manager.write.assert_called_once_with(model_name, {"minute": 2000, "tokens_used": 0})

def test_rate_limit_minute(rate_limit, mock_rate_limit_manager):
    mock_rate_limit_manager.read.return_value = {"minute": 3000, "tokens_used": 0}
    assert rate_limit.minute == 3000

def test_rate_limit_tokens_used(rate_limit, mock_rate_limit_manager):
    mock_rate_limit_manager.read.return_value = {"minute": 1000, "tokens_used": 500}
    assert rate_limit.tokens_used == 500

def test_ai_factory_create_payload(ai_factory, role_script, payload_data):
    payload = ai_factory.create_payload(
        prompt=payload_data["prompt"],
        role_script=role_script,
        temperature=payload_data["temperature"],
        max_tokens=payload_data["max_tokens"]
    )
    assert payload == {
        "model_name": ai_factory.model_name,
        "role_script": role_script.script,
        "prompt": payload_data["prompt"],
        "temperature": payload_data["temperature"],
        "max_tokens": payload_data["max_tokens"],
    }

def test_ai_factory_update_rate_limit_dict(ai_factory, mock_rate_limit_manager):
    tokens = 10
    ai_factory.update_rate_limit_dict(tokens)
    assert ai_factory.rate_limiter.rate_limit_dict["tokens_used"] == 10
    mock_rate_limit_manager.write.assert_called_once_with(
        ai_factory.model_name, {"minute": 1000, "tokens_used": 10}
    )

def test_ai_factory_modify_payload(ai_factory, payload_data):
    modified_payload = ai_factory.modify_payload(payload_data, test_key="test_value")
    expected_payload = payload_data.copy()
    expected_payload["test_key"] = "test_value"
    assert modified_payload == expected_payload

def test_ai_factory_enforce_rate_limit_within_limit(ai_factory, mock_rate_limit_manager):
    ai_factory.rate_limiter.rate_limit = 100
    mock_rate_limit_manager.read.return_value = {"minute": 1000, "tokens_used": 50}
    ai_factory._enforce_rate_limit(10, 30)
    assert ai_factory.rate_limiter.rate_limit_dict["tokens_used"] == 50

@patch("time.sleep")
def test_ai_factory_enforce_rate_limit_exceeds_limit(mock_sleep, ai_factory, mock_rate_limit_manager):
    ai_factory.rate_limiter.rate_limit = 100
    mock_rate_limit_manager.read.return_value = {"minute": time.time() - 55, "tokens_used": 90}
    ai_factory._enforce_rate_limit(10, 10)
    mock_sleep.assert_called_once()

@patch("time.sleep")
def test_ai_factory_cool_down(mock_sleep, ai_factory):
    minute = time.time() - 55
    ai_factory._cool_down(minute)
    mock_sleep.assert_called_once()

def test_ai_factory_error_handle(ai_factory):
    with pytest.raises(MaxRetryError):
        ai_factory._error_handle(MaxRetryError("Test error"), retry_count=3)
