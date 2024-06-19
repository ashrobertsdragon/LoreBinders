import pytest
from unittest.mock import patch, MagicMock

from src.lorebinders.ai_classes.exceptions import MissingAIProviderError
from src.lorebinders.ai_classes.ai_factory import AIModelConfig, AIInterface


@pytest.fixture
def mock_role_script() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_ai_models():
    return MagicMock(
        provider="mock_provider",
        models=MagicMock(
            get_model_by_id=lambda model_id: MagicMock(
                model_dump=lambda: {"model_key": "model_value"}
            )
        ),
    )


@pytest.fixture
def mock_ai_implementation():
    return MagicMock(
        set_model=lambda model_dict: None,
        call_api=lambda api_payload,
        json_response,
        retry_count,
        assistant_message: "Mock AI Response",
        create_payload=lambda prompt, role_script, temperature, max_tokens: {
            "model_name": "Mock Model",
            "prompt": prompt,
            "role_script": "Mock script",
            "max_tokens": 10,
            "temperature": temperature,
        },
    )


@pytest.fixture
def model_config(mock_ai_models):
    return AIModelConfig(mock_ai_models)


@pytest.fixture
def ai_interface(mock_ai_implementation):
    return AIInterface(mock_ai_implementation)


def test_ai_model_config_init(model_config):
    assert model_config.provider == "mock_provider"
    assert model_config.provider_models.provider == "mock_provider"


@patch("importlib.import_module")
def test_ai_model_config_initialize_api_valid(
    mock_import_module, model_config
):
    mock_import_module.return_value = MagicMock(
        MockAIImplementation=mock_ai_implementation()
    )

    ai_interface = model_config.initialize_api()
    assert isinstance(ai_interface, AIInterface)
    assert isinstance(ai_interface._ai, mock_ai_implementation())
    mock_import_module.assert_called_once_with(
        "api_mock_provider", package="ai_classes"
    )


def test_ai_model_config_initialize_api_invalid(model_config):
    model_config.provider = "invalid_provider"
    with pytest.raises(MissingAIProviderError) as excinfo:
        model_config.initialize_api()
    assert str(excinfo.value) == "Invalid AI provider: invalid_provider"


def test_ai_interface_set_model(model_config, ai_interface):
    model_id = 123
    ai_interface.set_model(model_config, model_id)
    models = model_config.provider_models.models
    get_model_by_id = models.get_model_by_id
    get_model_by_id.assert_called_once_with(model_id)
    ai_interface._ai.set_model.assert_called_once_with({
        "model_key": "model_value"
    })


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
        "temperature": temperature,
    }
    ai_interface._ai.create_payload.assert_called_once_with(
        prompt, role_script, temperature, max_tokens
    )
