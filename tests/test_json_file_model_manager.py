from _types import AIModelRegistry, APIProvider, Model, ModelFamily
from lorebinders.ai.exceptions import MissingModelFamilyError
from lorebinders.ai.ai_models.json_file_model_handler import (
    JSONFileProviderHandler,
)
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_ai_model_registry():
    return MagicMock(spec=AIModelRegistry)


@pytest.fixture
def file_handler(mock_ai_model_registry):
    handler = JSONFileProviderHandler()
    handler._registry = mock_ai_model_registry
    return handler


@patch("file_handling.read_json_file")
def test_load_registry(mock_read_json_file, file_handler):
    mock_read_json_file.return_value = {"test": "data"}
    registry = file_handler._load_registry()
    assert registry == mock_ai_model_registry
    mock_ai_model_registry.model_validate.assert_called_once_with({
        "test": "data"
    })


def test_get_all_providers(file_handler):
    file_handler.registry.providers = ["provider1", "provider2"]
    providers = file_handler.get_all_providers()
    assert providers == ["provider1", "provider2"]


def test_get_provider(file_handler):
    provider_name = "test_provider"
    file_handler.registry.get_provider.return_value = "test_provider_object"
    provider = file_handler.get_provider(provider_name)
    assert provider == "test_provider_object"
    file_handler.registry.get_provider.assert_called_once_with(provider_name)


@patch("file_handling.write_json_file")
def test_add_provider(mock_write_json_file, file_handler):
    provider = MagicMock(spec=APIProvider)
    file_handler.add_provider(provider)
    file_handler.registry.providers.append.assert_called_once_with(provider)
    mock_write_json_file.assert_called_once()


@patch("file_handling.write_json_file")
def test_delete_provider(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    file_handler.registry.providers = [
        MagicMock(name="test_provider"),
        MagicMock(name="another_provider"),
    ]
    file_handler.delete_provider(provider_name)
    mock_write_json_file.assert_called_once()
    assert len(file_handler.registry.providers) == 1
    assert file_handler.registry.providers[0].name == "another_provider"


@patch("file_handling.write_json_file")
def test_add_model_family(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    model_family = MagicMock(spec=ModelFamily)
    mock_provider = MagicMock(spec=APIProvider, model_families=[])
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.add_model_family(provider_name, model_family)
    mock_provider.model_families.append.assert_called_once_with(model_family)
    mock_write_json_file.assert_called_once()


@patch("file_handling.write_json_file")
def test_delete_model_family(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    mock_family = MagicMock(name="test_family")
    mock_provider = MagicMock(
        spec=APIProvider,
        model_families=[mock_family, MagicMock(name="another_family")],
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.delete_model_family(provider_name, family_name)
    mock_write_json_file.assert_called_once()
    assert len(mock_provider.model_families) == 1
    assert mock_provider.model_families[0].name == "another_family"


@patch("file_handling.write_json_file")
def test_add_model(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    model = MagicMock(spec=Model)
    mock_family = MagicMock(spec=ModelFamily, models=[])
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.add_model(provider_name, family_name, model)
    mock_family.models.append.assert_called_once_with(model)
    mock_write_json_file.assert_called_once()


@patch("file_handling.write_json_file")
def test_replace_model(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    model_id = 123
    model = MagicMock(spec=Model, id=None)
    mock_model1 = MagicMock(id=1)
    mock_model2 = MagicMock(id=123)
    mock_model3 = MagicMock(id=2)
    mock_family = MagicMock(
        spec=ModelFamily, models=[mock_model1, mock_model2, mock_model3]
    )
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.replace_model(model, model_id, family_name, provider_name)
    mock_write_json_file.assert_called_once()
    assert mock_family.models[1] == model
    assert model.id == model_id


@patch("file_handling.write_json_file")
def test_delete_model(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    model_id = 123
    mock_model1 = MagicMock(id=1)
    mock_model2 = MagicMock(id=123)
    mock_model3 = MagicMock(id=2)
    mock_family = MagicMock(
        spec=ModelFamily, models=[mock_model1, mock_model2, mock_model3]
    )
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.delete_model(provider_name, family_name, model_id)
    mock_write_json_file.assert_called_once()
    assert len(mock_family.models) == 2
    assert all(m.id != model_id for m in mock_family.models)


@patch("file_handling.write_json_file")
def test_write_registry_to_file(mock_write_json_file, file_handler):
    file_handler.registry.model_dump.return_value = {"test": "data"}
    file_handler._write_registry_to_file()
    mock_write_json_file.assert_called_once_with(
        {"test": "data"}, "ai_models.json"
    )


def test_get_model_family_not_found(file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    mock_provider = MagicMock(
        spec=APIProvider, get_model_family=lambda family: None
    )
    file_handler.registry.get_provider.return_value = mock_provider

    with pytest.raises(MissingModelFamilyError) as excinfo:
        file_handler.get_model_family(provider_name, family_name)

    assert (
        str(excinfo.value)
        == f"No model family {family_name} found for provider {provider_name}"
    )
