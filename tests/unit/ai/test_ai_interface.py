import pytest
from unittest.mock import patch, MagicMock, create_autospec

from lorebinders.ai.exceptions import MissingAIProviderError
from lorebinders.ai.ai_interface import AIModelConfig, AIInterface
from lorebinders.ai.ai_type import AIType


@pytest.fixture
def mock_api_provider():
    return MagicMock(api="mock_provider")


@pytest.fixture
def mock_ai_models(mock_api_provider):
    models = MagicMock()
    models.api = mock_api_provider.api
    models.get_ai_family.return_value = MagicMock(
        get_model_by_id=MagicMock(return_value=MagicMock(model_dump=lambda: {"model_key": "model_value"}))
    )
    return models


@pytest.fixture
def mock_ai_implementation():
    implementation = create_autospec(AIType)
    implementation.call_api.return_value = "Mock AI Response"
    implementation.create_payload.return_value = {
        "model_name": "Mock Model",
        "prompt": "Test prompt",
        "role_script": "Mock script",
        "max_tokens": 10,
        "temperature": 0.5,
    }
    return implementation


@pytest.fixture
def model_config(mock_ai_models):
    return AIModelConfig(mock_ai_models)


@pytest.fixture
def mock_rate_limiter():
    return MagicMock()


@pytest.fixture
def ai_interface(mock_ai_implementation, mock_rate_limiter):
    return AIInterface(mock_ai_implementation, mock_rate_limiter)


def test_ai_model_config_init(model_config):
    assert model_config.provider == "mock_provider"
    assert model_config.api_provider.api == "mock_provider"


@patch("importlib.import_module")
def test_ai_model_config_initialize_api_valid(mock_import_module, model_config, mock_rate_limiter):
    mock_provider_api = create_autospec(AIType)
    mock_import_module.return_value = MagicMock(MockProviderAPI=mock_provider_api)

    ai_interface = model_config.initialize_api(mock_rate_limiter)

    assert isinstance(ai_interface, AIInterface)
    assert isinstance(ai_interface._ai, MagicMock)
    mock_import_module.assert_called_once_with(
        "api_mock_provider", package="ai.ai_classes"
    )


def test_ai_model_config_initialize_api_invalid(model_config):
    model_config.provider = "invalid_provider"
    with pytest.raises(MissingAIProviderError) as excinfo:
        model_config.initialize_api(mock_rate_limiter)
    assert str(excinfo.value) == "Invalid AI provider: invalid_provider"


def test_ai_interface_set_family(ai_interface, model_config):
    family = "test_family"
    ai_interface.set_family(model_config, family)
    model_config.api_provider.get_ai_family.assert_called_once_with(family)


def test_ai_interface_set_model(ai_interface, mock_rate_limiter):
    model_id = 123
    ai_interface._family = MagicMock()
    ai_interface.set_model(model_id)
    ai_interface._family.get_model_by_id.assert_called_once_with(model_id)
    ai_interface._ai.set_model.assert_called_once_with(
        ai_interface._family.get_model_by_id.return_value,
        mock_rate_limiter
    )


def test_ai_interface_call_api(ai_interface):
    api_payload = {"test": "data"}
    response = ai_interface.call_api(api_payload)
    assert response == "Mock AI Response"
    ai_interface._ai.call_api.assert_called_once_with(
        api_payload, False, 0, None
    )


def test_ai_interface_create_payload(ai_interface):
    prompt = "Test prompt"
    role_script = "Test role script"
    temperature = 0.5
    max_tokens = 50
    payload = ai_interface.create_payload(
        prompt, role_script, temperature, max_tokens
    )
    assert payload == {
        "model_name": "Mock Model",
        "prompt": prompt,
        "role_script": "Mock script",
        "max_tokens": 10,
        "temperature": temperature,
    }
    ai_interface._ai.create_payload.assert_called_once_with(
        prompt, role_script, temperature, max_tokens
    )
