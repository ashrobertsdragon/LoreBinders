from json import JSONDecodeError
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from lorebinders.ai.ai_models._model_schema import AIModelRegistry, APIProvider, Model, ModelFamily
from lorebinders.ai.exceptions import MissingModelFamilyError
from lorebinders.ai.ai_models.json_file_model_handler import (
    JSONFileProviderHandler,
)


@pytest.fixture
def mock_ai_model_registry():
    return MagicMock(spec=AIModelRegistry, providers=[])


@pytest.fixture
def file_handler(mock_ai_model_registry):
    mock_directory = "test_directory"
    handler = JSONFileProviderHandler(mock_directory)
    handler._registry = mock_ai_model_registry
    return handler


@patch("lorebinders.ai.ai_models.json_file_model_handler.read_json_file")
@patch("lorebinders.ai.ai_models.json_file_model_handler.AIModelRegistry")
def test_load_registry(mock_ai_model_registry_class, mock_read_json_file, file_handler, mock_ai_model_registry):
    mock_model_validate = MagicMock(        return_value = mock_ai_model_registry)
    mock_ai_model_registry_class.model_validate = mock_model_validate
    mock_read_json_file.return_value = {"test": "data"}
    registry = file_handler._load_registry()
    mock_model_validate.assert_called_once_with({
        "test": "data"
    })
    assert registry is mock_ai_model_registry

@patch("lorebinders.ai.ai_models.json_file_model_handler.read_json_file")
def test_load_registry_raises_exception(mock_read_json_file):
    mock_directory = "test_directory"
    mock_read_json_file.side_effect = JSONDecodeError("", "", 0)
    handler = JSONFileProviderHandler(mock_directory)
    with pytest.raises(JSONDecodeError):
        _ = handler.registry

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


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_add_provider(mock_write_json_file, file_handler):
    provider = MagicMock(spec=APIProvider, api="test_provider")
    file_handler.add_provider(provider)
    assert file_handler.registry.providers[0] ==(provider)
    mock_write_json_file.assert_called_once()


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_delete_provider(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    file_handler.registry.providers = [
        MagicMock(api="test_provider"),
        MagicMock(api="another_provider"),
    ]
    file_handler.delete_provider(provider_name)
    mock_write_json_file.assert_called_once()
    assert len(file_handler.registry.providers) == 1
    assert file_handler.registry.providers[0].api == "another_provider"


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_add_ai_family(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    ai_family = MagicMock(spec=ModelFamily)
    mock_provider = MagicMock(spec=APIProvider, ai_families=[])
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.add_ai_family(provider_name, ai_family)
    assert mock_provider.ai_families[0] ==(ai_family)
    mock_write_json_file.assert_called_once()


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_delete_ai_family(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    mock_family = MagicMock(family="test_family")
    mock_provider = MagicMock(
        spec=APIProvider,
        ai_families=[mock_family, MagicMock(family="another_family")],
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.delete_ai_family(provider_name, family_name)
    mock_write_json_file.assert_called_once()
    assert len(mock_provider.ai_families) == 1
    assert mock_provider.ai_families[0].family == "another_family"


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_add_model(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    model = MagicMock(spec=Model)
    mock_family = MagicMock(spec=ModelFamily, models=[])
    mock_provider = MagicMock(
        spec=APIProvider,
        get_ai_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.add_model(provider_name, family_name, model)
    assert mock_family.models[0] == model
    mock_write_json_file.assert_called_once()


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
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
        get_ai_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.replace_model(model, model_id, family_name, provider_name)
    mock_write_json_file.assert_called_once()
    assert mock_family.models[1] == model
    assert model.id == model_id


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_delete_model(mock_write_json_file, file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    model_id = 3
    mock_model1 = MagicMock(id=1)
    mock_model2 = MagicMock(id=2)
    mock_model3 = MagicMock(id=3)
    mock_family = MagicMock(
        spec=ModelFamily, models=[mock_model1, mock_model2, mock_model3]
    )
    mock_provider = MagicMock(
        spec=APIProvider,
        get_ai_family=lambda family: mock_family
        if family == family_name
        else None,
    )
    file_handler.registry.get_provider.return_value = mock_provider
    file_handler.delete_model(provider_name, family_name, model_id)
    mock_write_json_file.assert_called_once()
    assert len(mock_family.models) == 2
    assert all(m.id != model_id for m in mock_family.models)


@patch("lorebinders.ai.ai_models.json_file_model_handler.write_json_file")
def test_write_registry_to_file(mock_write_json_file, file_handler):
    file_handler.registry.model_dump.return_value = {"test": "data"}
    file_handler._write_registry_to_file()
    mock_write_json_file.assert_called_once_with(
        {"test": "data"}, Path("test_directory/ai_models.json")
    )

def test_get_ai_family(file_handler):
    provider_name = "test_provider"
    family_name = "test_family 2"
    mock_family_1 = MagicMock(family="test_family 1")
    mock_family_2 = MagicMock(family="test_family 2")
    mock_family_3 = MagicMock(family="test_family 3")
    mock_provider = MagicMock(
        spec=APIProvider, api=provider_name,ai_families=[mock_family_1, mock_family_2, mock_family_3])
    file_handler.get_provider = MagicMock(return_value=mock_provider)
    mock_provider.get_ai_family = MagicMock(return_value=mock_family_2)
    assert file_handler.get_ai_family(provider_name, family_name) == mock_family_2


def test_get_ai_family_not_found(file_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    mock_provider = MagicMock(
        spec=APIProvider, get_ai_family=lambda family: None
    )
    file_handler.registry.get_provider.return_value = mock_provider

    with pytest.raises(MissingModelFamilyError, match="No model family test_family found for provider test_provider"):
        file_handler.get_ai_family(provider_name, family_name)
