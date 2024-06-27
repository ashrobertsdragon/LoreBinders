import time
from pydantic import BaseModel
from lorebinders._managers import EmailManager, RateLimitManager
from lorebinders.ai.exceptions import MaxRetryError

import pytest
from unittest.mock import patch, MagicMock
from lorebinders.ai.ai_factory import RateLimit, AIFactory
from lorebinders.attributes import RoleScript
from lorebinders.ai.api_error_handler import APIErrorHandler


@pytest.fixture
def mock_rate_limit_manager():
    return MagicMock(spec=RateLimitManager)


@pytest.fixture
def mock_email_manager():
    return MagicMock(spec=EmailManager)


@pytest.fixture
def mock_model():
    return MagicMock(model="test_model")


@pytest.fixture
def rate_limit(mock_model, mock_rate_limit_manager):
    return RateLimit(mock_model.model, mock_rate_limit_manager)


@pytest.fixture
def ai_factory(mock_email_manager, mock_rate_limit_manager, mock_model):
    ai_factory = MagicMock(spec=AIFactory)
    ai_factory.model = mock_model
    ai_factory.model_name = mock_model.model
    ai_factory.tokenizer = MagicMock()
    ai_factory.rate_limiter = RateLimit(
        mock_model.model, mock_rate_limit_manager
    )
    ai_factory.error_handler = APIErrorHandler(
        email_manager=mock_email_manager, unresolvable_errors=(MaxRetryError,)
    )
    return ai_factory


@pytest.fixture
def mock_ai_implementation():
    return MagicMock(
        set_model=lambda model_dict: None,
        create_payload=lambda prompt, role_script, temperature, max_tokens: {
            "model_name": "Mock Model",
            "prompt": prompt,
            "temperature": temperature,
            "role_script": role_script.script,
            "max_tokens": role_script.max_tokens,
        },
        preprocess_response=lambda response: ("Mock Content", 10, "stop"),
        process_response=lambda content_tuple,
        assistant_message,
        api_payload,
        retry_count,
        json_response: "Processed Response",
    )


@pytest.fixture
def mock_payload():
    class MockPayload(BaseModel):
        model_name: str = "test_model"
        role_script: str = "test_script"
        prompt: str = "test_prompt"
        temperature: float = 1.0
        max_tokens: int = 100

    return MockPayload()


def test_rate_limit_init(rate_limit, mock_model, mock_rate_limit_manager):
    assert rate_limit.model == mock_model.model
    assert rate_limit._rate_handler == mock_rate_limit_manager
    mock_rate_limit_manager.read.assert_called_once_with(mock_model.model)


def test_rate_limit_read_rate_limit_dict(rate_limit, mock_rate_limit_manager):
    rate_limit.read_rate_limit_dict()
    mock_rate_limit_manager.read.assert_called_once_with(rate_limit.model)


def test_rate_limit_update_rate_limit_dict(
    rate_limit, mock_rate_limit_manager
):
    rate_limit.update_rate_limit_dict()
    mock_rate_limit_manager.write.assert_called_once_with(
        rate_limit.model, rate_limit.rate_limit_dict
    )


def test_rate_limit_reset_rate_limit_dict(rate_limit, mock_rate_limit_manager):
    rate_limit.reset_rate_limit_dict()
    assert rate_limit.rate_limit_dict["minute"] == pytest.approx(time.time())
    assert rate_limit.rate_limit_dict["tokens_used"] == 0
    mock_rate_limit_manager.write.assert_called_once_with(
        rate_limit.model, rate_limit.rate_limit_dict
    )


def test_rate_limit_minute(rate_limit):
    assert rate_limit.minute == pytest.approx(
        rate_limit.rate_limit_dict["minute"]
    )


def test_rate_limit_tokens_used(rate_limit):
    assert rate_limit.tokens_used == rate_limit.rate_limit_dict["tokens_used"]


def test_ai_factory_set_model(ai_factory, mock_model, mock_rate_limit_manager):
    ai_factory.set_model(mock_model, mock_rate_limit_manager)
    assert ai_factory.model == mock_model
    assert ai_factory.model_name == mock_model.model
    assert ai_factory.rate_limiter.model == mock_model.model
    assert ai_factory.rate_limiter._rate_handler == mock_rate_limit_manager


def test_ai_factory_create_payload(ai_factory, mock_payload):
    prompt = "Test prompt"
    role_script = RoleScript(script="Test role script", max_tokens=50)
    temperature = 0.5
    max_tokens = 100
    payload = ai_factory.create_payload(
        prompt, role_script, temperature, max_tokens
    )
    assert payload == {
        "model_name": "test_model",
        "role_script": "Test role script",
        "prompt": "Test prompt",
        "temperature": 0.5,
        "max_tokens": 100,
    }


def test_ai_factory_update_rate_limit_dict(
    ai_factory, mock_rate_limit_manager
):
    tokens = 10
    ai_factory.update_rate_limit_dict(tokens)
    assert ai_factory.rate_limiter.rate_limit_dict["tokens_used"] == tokens
    mock_rate_limit_manager.write.assert_called_once_with(
        "test_model", ai_factory.rate_limiter.rate_limit_dict
    )


def test_ai_factory_modify_payload(ai_factory, mock_payload):
    api_payload = mock_payload.model_dump()
    modified_payload = ai_factory.modify_payload(
        api_payload, test_key="test_value"
    )
    assert modified_payload == {
        "model_name": "test_model",
        "role_script": "test_script",
        "prompt": "test_prompt",
        "temperature": 1.0,
        "max_tokens": 100,
        "test_key": "test_value",
    }


def test_ai_factory_enforce_rate_limit_within_limit(ai_factory):
    ai_factory.rate_limiter.rate_limit = 100
    ai_factory.rate_limiter.rate_limit_dict["tokens_used"] = 50
    ai_factory._enforce_rate_limit(10, 100)
    assert ai_factory.rate_limiter.rate_limit_dict["tokens_used"] == 50


@patch("time.sleep")
def test_ai_factory_enforce_rate_limit_exceeds_limit(mock_sleep, ai_factory):
    ai_factory.rate_limiter.rate_limit = 100
    ai_factory.rate_limiter.rate_limit_dict["tokens_used"] = 90
    ai_factory.rate_limiter.rate_limit_dict["minute"] = time.time() - 55
    ai_factory._enforce_rate_limit(10, 100)
    mock_sleep.assert_called_once_with(5)


@patch("time.sleep")
def test_ai_factory_cool_down(mock_sleep, ai_factory):
    minute = time.time() - 55
    ai_factory._cool_down(minute)
    mock_sleep.assert_called_once_with(5)
