from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._types import AIModelRegistry, APIProvider, Model, ModelFamily
from lorebinders.ai.exceptions import MissingModelFamilyError
from lorebinders.ai.ai_models.sqlite_model_handler import (
    SQLiteProviderHandler,
)
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_ai_model_registry():
    return MagicMock(spec=AIModelRegistry)


@pytest.fixture
def sqlite_provider_handler(mock_ai_model_registry):
    handler = SQLiteProviderHandler()
    handler._registry = mock_ai_model_registry
    return handler


@patch("sqlite3.connect")
def test_initialize_database(mock_connect, sqlite_provider_handler):
    sqlite_provider_handler._initialize_database()
    mock_connect.assert_called_once_with("ai_models.db")
    mock_connect.return_value.cursor.return_value.execute.assert_has_calls([
        pytest.approx(
            """
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """
        ),
        pytest.approx(
            """
                CREATE TABLE IF NOT EXISTS model_families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    FOREIGN KEY(provider_name) REFERENCES providers(name)
                )
            """
        ),
        pytest.approx(
            """
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    context_window INTEGER NOT NULL,
                    rate_limit INTEGER NOT NULL,
                    tokenizer TEXT NOT NULL,
                    family TEXT NOT NULL,
                    PRIMARY KEY(id, family_name),
                    FOREIGN KEY(family_name) REFERENCES model_families(family)
                )
            """
        ),
    ])


@patch("sqlite3.connect")
def test_execute_query(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{"test": "data"}]
    result = sqlite_provider_handler._execute_query("SELECT * FROM test_table")
    assert result == [{"test": "data"}]
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table")


@patch("sqlite3.connect")
def test_execute_query_with_params(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{"test": "data"}]
    result = sqlite_provider_handler._execute_query(
        "SELECT * FROM test_table WHERE id = ?", (1,)
    )
    assert result == [{"test": "data"}]
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM test_table WHERE id = ?", (1,)
    )


@patch("sqlite3.connect")
def test_registry_query(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "provider": "test_provider",
            "provider_name": "test_provider",
            "family": "test_family",
            "id": 123,
            "name": "test_model",
            "context_window": 1000,
            "rate_limit": 10,
            "tokenizer": "gpt2",
        }
    ]
    result = sqlite_provider_handler._registry_query()
    assert result == [
        {
            "provider": "test_provider",
            "provider_name": "test_provider",
            "family": "test_family",
            "id": 123,
            "name": "test_model",
            "context_window": 1000,
            "rate_limit": 10,
            "tokenizer": "gpt2",
        }
    ]


@patch("sqlite3.connect")
def test_process_db_response(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "provider": "test_provider",
            "provider_name": "test_provider",
            "family": "test_family",
            "id": 123,
            "name": "test_model",
            "context_window": 1000,
            "rate_limit": 10,
            "tokenizer": "gpt2",
        }
    ]
    result = sqlite_provider_handler._process_db_response(
        sqlite_provider_handler._registry_query()
    )
    assert result == [
        {
            "name": "test_provider",
            "model_families": [
                {
                    "family": "test_family",
                    "models": [
                        {
                            "id": 123,
                            "name": "test_model",
                            "context_window": 1000,
                            "rate_limit": 10,
                            "tokenizer": "gpt2",
                        }
                    ],
                }
            ],
        }
    ]


@patch("sqlite3.connect")
def test_load_registry(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "provider": "test_provider",
            "provider_name": "test_provider",
            "family": "test_family",
            "id": 123,
            "name": "test_model",
            "context_window": 1000,
            "rate_limit": 10,
            "tokenizer": "gpt2",
        }
    ]
    registry = sqlite_provider_handler._load_registry()
    assert registry == mock_ai_model_registry
    mock_ai_model_registry.model_validate.assert_called_once_with([
        {
            "name": "test_provider",
            "model_families": [
                {
                    "family": "test_family",
                    "models": [
                        {
                            "id": 123,
                            "name": "test_model",
                            "context_window": 1000,
                            "rate_limit": 10,
                            "tokenizer": "gpt2",
                        }
                    ],
                }
            ],
        }
    ])


def test_get_all_providers(sqlite_provider_handler):
    sqlite_provider_handler.registry.providers = ["provider1", "provider2"]
    providers = sqlite_provider_handler.get_all_providers()
    assert providers == ["provider1", "provider2"]


def test_get_provider(sqlite_provider_handler):
    provider_name = "test_provider"
    sqlite_provider_handler.registry.get_provider.return_value = (
        "test_provider_object"
    )
    provider = sqlite_provider_handler.get_provider(provider_name)
    assert provider == "test_provider_object"
    sqlite_provider_handler.registry.get_provider.assert_called_once_with(
        provider_name
    )


@patch("sqlite3.connect")
def test_add_provider(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider = MagicMock(
        spec=APIProvider, name="test_provider", model_families=[]
    )
    sqlite_provider_handler.add_provider(provider)
    mock_cursor.execute.assert_has_calls([
        pytest.approx(
            "INSERT INTO providers (name) VALUES (?)", ("test_provider",)
        )
    ])
    sqlite_provider_handler.registry.providers.append.assert_called_once_with(
        provider
    )


@patch("sqlite3.connect")
def test_delete_provider(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    sqlite_provider_handler.registry.providers = [
        MagicMock(name="test_provider"),
        MagicMock(name="another_provider"),
    ]
    sqlite_provider_handler.delete_provider(provider_name)
    mock_cursor.execute.assert_called_once_with(
        "DELETE FROM providers WHERE name = ?", ("test_provider",)
    )
    assert len(sqlite_provider_handler.registry.providers) == 1
    assert (
        sqlite_provider_handler.registry.providers[0].name
        == "another_provider"
    )


@patch("sqlite3.connect")
def test_get_model_family(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    family_name = "test_family"
    model_family = MagicMock(spec=ModelFamily)
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: model_family
        if family == family_name
        else None,
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    result = sqlite_provider_handler.get_model_family(
        provider_name, family_name
    )
    assert result == model_family
    sqlite_provider_handler.registry.get_provider.assert_called_once_with(
        provider_name
    )


def test_get_model_family_not_found(sqlite_provider_handler):
    provider_name = "test_provider"
    family_name = "test_family"
    mock_provider = MagicMock(
        spec=APIProvider, get_model_family=lambda family: None
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    with pytest.raises(MissingModelFamilyError) as excinfo:
        sqlite_provider_handler.get_model_family(provider_name, family_name)
    assert (
        str(excinfo.value)
        == f"No family {family_name} found for provider {provider_name}"
    )


@patch("sqlite3.connect")
def test_add_model_family(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    model_family = MagicMock(spec=ModelFamily, family="test_family", models=[])
    mock_provider = MagicMock(
        spec=APIProvider, model_families=[], name="test_provider"
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    sqlite_provider_handler.add_model_family(provider_name, model_family)
    mock_cursor.execute.assert_has_calls([
        pytest.approx(
            "INSERT INTO model_families (family, provider_name) VALUES (?, ?)",
            ("test_family", "test_provider"),
        )
    ])
    mock_provider.model_families.append.assert_called_once_with(model_family)


@patch("sqlite3.connect")
def test_delete_model_family(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    family_name = "test_family"
    mock_family = MagicMock(family="test_family")
    mock_provider = MagicMock(
        spec=APIProvider,
        model_families=[mock_family, MagicMock(family="another_family")],
        name="test_provider",
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    sqlite_provider_handler.delete_model_family(provider_name, family_name)
    mock_cursor.execute.assert_called_once_with(
        "DELETE FROM model_families WHERE name = ? AND provider_name = ?",
        ("test_family", "test_provider"),
    )
    assert len(mock_provider.model_families) == 1
    assert mock_provider.model_families[0].family == "another_family"


@patch("sqlite3.connect")
def test_add_model(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    family_name = "test_family"
    model = MagicMock(
        spec=Model,
        name="test_model",
        context_window=1000,
        rate_limit=10,
        tokenizer="gpt2",
        id=123,
    )
    mock_family = MagicMock(spec=ModelFamily, family="test_family", models=[])
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
        name="test_provider",
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    sqlite_provider_handler.add_model(provider_name, family_name, model)
    mock_cursor.execute.assert_has_calls([
        pytest.approx(
            """
            INSERT INTO models (
                id, name, context_window, rate_limit, tokenizer, family
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                123,
                "test_model",
                1000,
                10,
                "gpt2",
                "test_family",
            ),
        )
    ])
    mock_family.models.append.assert_called_once_with(model)


@patch("sqlite3.connect")
def test_replace_model(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    family_name = "test_family"
    model_id = 123
    model = MagicMock(
        spec=Model,
        name="test_model",
        context_window=1000,
        rate_limit=10,
        tokenizer="gpt2",
        id=None,
    )
    mock_model1 = MagicMock(id=1)
    mock_model2 = MagicMock(id=123)
    mock_model3 = MagicMock(id=2)
    mock_family = MagicMock(
        spec=ModelFamily,
        family="test_family",
        models=[mock_model1, mock_model2, mock_model3],
    )
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
        name="test_provider",
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    sqlite_provider_handler.replace_model(
        model, model_id, family_name, provider_name
    )
    mock_cursor.execute.assert_has_calls([
        pytest.approx(
            """
            UPDATE models SET (
                name = ?, context_window = ?, rate_limit = ?, tokenizer = ?
            ) WHERE id = ? AND family = ?
            """,
            (
                "test_model",
                1000,
                10,
                "gpt2",
                123,
                "test_family",
            ),
        )
    ])
    assert mock_family.models[1] == model
    assert model.id == model_id


@patch("sqlite3.connect")
def test_delete_model(mock_connect, sqlite_provider_handler):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    provider_name = "test_provider"
    family_name = "test_family"
    model_id = 123
    mock_model1 = MagicMock(id=1)
    mock_model2 = MagicMock(id=123)
    mock_model3 = MagicMock(id=2)
    mock_family = MagicMock(
        spec=ModelFamily,
        family="test_family",
        models=[mock_model1, mock_model2, mock_model3],
    )
    mock_provider = MagicMock(
        spec=APIProvider,
        get_model_family=lambda family: mock_family
        if family == family_name
        else None,
        name="test_provider",
    )
    sqlite_provider_handler.registry.get_provider.return_value = mock_provider
    sqlite_provider_handler.delete_model(provider_name, family_name, model_id)
    mock_cursor.execute.assert_called_once_with(
        "DELETE FROM models WHERE id = ? AND family = ?",
        (123, "test_family"),
    )
    assert len(mock_family.models) == 2
    assert all(m.id != model_id for m in mock_family.models)


@patch("sqlite3.connect")
def test_get_model_attr(mock_connect, sqlite_provider_handler):
    model = MagicMock(
        name="test_model",
        context_window=1000,
        rate_limit=10,
        tokenizer="gpt2",
        id=123,
    )
    name, context_window, rate_limit, tokenizer, model_id = (
        sqlite_provider_handler.get_model_attr(model)
    )
    assert name == "test_model"
    assert context_window == 1000
    assert rate_limit == 10
    assert tokenizer == "gpt2"
    assert model_id == 123
