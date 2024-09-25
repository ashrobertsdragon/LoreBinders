from pathlib import Path
from unittest.mock import patch, MagicMock

from pydantic import ValidationError
import pytest

from lorebinders.ai.exceptions import MissingModelFamilyError
from lorebinders.ai.ai_models._model_schema import AIModelRegistry, APIProvider, Model, ModelFamily
from lorebinders.ai.ai_models.sqlite_model_handler import (
    SQLiteProviderHandler, SQLite, DatabaseOperationError
)

@pytest.fixture
def mock_ai_model_registry():
    return MagicMock(spec=AIModelRegistry)

@pytest.fixture
def mock_sqlite3():
    with patch("lorebinders.ai.ai_models.sqlite_model_handler.sqlite3") as mock:
        mock.Error = type("Error", (Exception,), {})
        yield mock


@pytest.fixture
def mock_sqlite():
    with patch("lorebinders.ai.ai_models.sqlite_model_handler.SQLite") as mock:
        yield mock

@pytest.fixture
def mock_sqlite_transaction(mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor
    return mock_cursor

@pytest.fixture
def test_handler():
    return SQLiteProviderHandler("test.db")

@pytest.fixture(scope="function")
def test_registry():
    return AIModelRegistry.model_construct(
        providers=[
            APIProvider(
                api="OpenAI",
                ai_families=[
                    ModelFamily(
                        family="GPT",
                        tokenizer="tiktoken",
                        models=[
                            Model(name="GPT-3.5-Turbo", api_model="gpt-3.5-turbo", context_window=4096, rate_limit=3500),
                            Model(name="GPT-4", api_model="gpt-4", context_window=8192, rate_limit=200),
                            Model(name="GPT-4-Turbo", api_model="gpt-4-turbo-preview", context_window=128000, rate_limit=150),
                        ]
                    )
                ]
            ),
            APIProvider(
                api="Anthropic",
                ai_families=[
                    ModelFamily(
                        family="Claude",
                        tokenizer="claude_tokenizer",
                        models=[
                            Model(name="Claude 2", api_model="claude-2", context_window=100000, rate_limit=15),
                            Model(name="Claude 3 Opus", api_model="claude-3-opus-20240229", context_window=200000, rate_limit=10),
                            Model(name="Claude 3 Sonnet", api_model="claude-3-sonnet-20240229", context_window=200000, rate_limit=20),
                        ]
                    )
                ]
            ),
            APIProvider(
                api="Google",
                ai_families=[
                    ModelFamily(
                        family="PaLM",
                        tokenizer="sentencepiece",
                        models=[
                            Model(name="PaLM 2 Chat", api_model="chat-bison-001", context_window=8192, rate_limit=60),
                            Model(name="PaLM 2 Text", api_model="text-bison-001", context_window=8192, rate_limit=60),
                            Model(name="Gemini Pro", api_model="gemini-pro", context_window=32768, rate_limit=60),
                        ]
                    )
                ]
            )
        ]
    )

def test_sqlite3_successful_operation(mock_sqlite3):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor

    with SQLite("test.db") as cursor:
        assert cursor == mock_cursor

    mock_sqlite3.connect.assert_called_once_with("test.db")
    mock_connection.commit.assert_called_once()
    mock_connection.close.assert_called_once()

def test_sqlite3_exception_in_context(mock_sqlite3):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor

    with pytest.raises(ValueError):
        with SQLite("test.db") as cursor:
            raise ValueError("Test exception")

    mock_connection.rollback.assert_called_once()
    mock_connection.close.assert_called_once()

def test_sqlite3_connection_closed_on_success(mock_sqlite3):
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection

    with SQLite("test.db"):
        pass

    mock_connection.close.assert_called_once()

def test_sqlite3_connection_closed_on_exception(mock_sqlite3):
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection

    with pytest.raises(ValueError):
        with SQLite("test.db"):
            raise ValueError("Test exception")

    mock_connection.close.assert_called_once()

def test_sqlite3_database_operation_error(mock_sqlite3):
    mock_connect = MagicMock(side_effect = mock_sqlite3.Error("Database error"))
    mock_sqlite3.connect = mock_connect

    with pytest.raises(DatabaseOperationError):
        with SQLite("test.db"):
            pass


def test_create_tables_success(test_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor

    test_handler._create_tables()

    mock_sqlite.assert_called_once_with(test_handler.db)
    assert mock_cursor.execute.call_count == 3
    calls = mock_cursor.execute.call_args_list
    assert "CREATE TABLE IF NOT EXISTS providers" in calls[0][0][0]
    assert "CREATE TABLE IF NOT EXISTS ai_families" in calls[1][0][0]
    assert "CREATE TABLE IF NOT EXISTS models" in calls[2][0][0]

@patch("lorebinders.ai.ai_models.sqlite_model_handler.logger")
def test_create_tables_logs_success(mock_logger, test_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor

    test_handler._create_tables()

    mock_logger.info.assert_called_once_with("Database initialized")

@patch("lorebinders._decorators.logger")
def test_create_tables_logs_error(mock_logger, test_handler, mock_sqlite):
    mock_sqlite.side_effect = DatabaseOperationError("SQLite error")

    with pytest.raises(DatabaseOperationError):
        test_handler._create_tables()
    mock_logger.exception.assert_called_once()

def test_init_with_custom_filename():
    schema_directory = "/path/to/schema"
    custom_filename = "custom.db"
    handler = SQLiteProviderHandler(schema_directory, schema_filename=custom_filename)

    assert handler.db == Path(schema_directory, custom_filename)
    assert handler._registry is None

def test_init_with_default_filename():
    schema_directory = "/path/to/schema"
    handler = SQLiteProviderHandler(schema_directory)

    assert handler.db == Path(schema_directory, "ai_models.db")
    assert handler._registry is None

def test_execute_query_without_params(test_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("result1",), ("result2",)]

    result = test_handler._execute_query("SELECT * FROM test_table")

    mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table")
    assert result == [("result1",), ("result2",)]

def test_execute_query_with_params(test_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("result1",)]

    result = test_handler._execute_query("SELECT * FROM test_table WHERE id = ?", (1,))

    mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table WHERE id = ?", (1,))
    assert result == [("result1",)]

def test_execute_query_database_operation_error(caplog, test_handler, mock_sqlite_transaction):
    import logging # shut up the stack trace
    mock_execute = MagicMock(side_effect = DatabaseOperationError("Database error"))
    mock_sqlite_transaction.execute = mock_execute

    with pytest.raises(DatabaseOperationError), caplog.at_level(logging.ERROR):
        test_handler._execute_query("SELECT * FROM test_table")

@patch("lorebinders._decorators.logger")
def test_execute_query_logs_exception(mock_logger, test_handler, mock_sqlite_transaction):
    mock_execute = MagicMock(side_effect = DatabaseOperationError("Database error"))
    mock_sqlite_transaction.execute = mock_execute

    with pytest.raises(DatabaseOperationError):
        test_handler._execute_query("SELECT * FROM test_table")

    mock_logger.exception.assert_called_once()


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_registry_query(mock_execute_query, test_handler):
    mock_execute_query.return_value = [{"provider": "provider1", "api": "api1", "family": "family1", "tokenizer": "tokenizer1"}, {"provider": "provider2", "api": "api2", "family": "family2", "tokenizer": "tokenizer2"}]
    result = test_handler._registry_query()

    assert result == [
        {
            "provider": "provider1",
            "api": "api1",
            "family": "family1",
            "tokenizer": "tokenizer1",
        },
        {
            "provider": "provider2",
            "api": "api2",
            "family": "family2",
            "tokenizer": "tokenizer2",
        },
    ]

def test_process_db_response_with_valid_data(test_handler):
    data = [
        {
            "provider": "provider1",
            "family": "family1",
            "id": 1,
            "name": "Model One",
            "api_model": "api_model1",
            "context_window": 2048,
            "rate_limit": 100,
            "tokenizer": "tokenizer1"
        },
        {
            "provider": "provider1",
            "family": "family1",
            "id": 2,
            "name": "Model Two",
            "api_model": "api_model2",
            "context_window": 4096,
            "rate_limit": 200,
            "tokenizer": "tokenizer1"
        }
    ]
    expected_output = [
        {
            "api": "provider1",
            "ai_families": [
                {
                    "family": "family1",
                    "tokenizer": "tokenizer1",
                    "models": [
                        {
                            "id": 1,
                            "name": "Model One",
                            "api_model": "api_model1",
                            "context_window": 2048,
                            "rate_limit": 100
                        },
                        {
                            "id": 2,
                            "name": "Model Two",
                            "api_model": "api_model2",
                            "context_window": 4096,
                            "rate_limit": 200
                        }
                    ]
                }
            ]
        }
    ]
    result = test_handler._process_db_response(data)
    assert result == expected_output

def test_process_db_response_with_empty_data(test_handler):
    data = []
    expected_output = []
    result = test_handler._process_db_response(data)
    assert result == expected_output

@pytest.mark.parametrize(
    ("check_return_value", "create_is_called"),
    [
        (["providers", "ai_families", "models"], False),
        ([], True),
        (["providers", "ai_families"], True),
    ]
)
@patch.object(SQLiteProviderHandler, "_execute_query")
@patch.object(SQLiteProviderHandler, "_create_tables")
def test_check_for_tables(mock_create_tables, mock_execute_query, check_return_value, create_is_called, test_handler):
    mock_execute_query.return_value = check_return_value
    test_handler._check_for_tables()
    assert mock_create_tables.called == create_is_called


@patch.object(SQLiteProviderHandler, "_check_for_tables")
@patch.object(SQLiteProviderHandler, "_registry_query")
@patch.object(SQLiteProviderHandler, "_process_db_response")
@patch("lorebinders.ai.ai_models.sqlite_model_handler.AIModelRegistry")
def test_load_registry_happy_path(mock_registry, mock_process_db_response, mock_registry_query, mock_check_for_tables, test_handler):
    mock_validate = MagicMock()
    mock_registry.model_validate = mock_validate
    mock_db_response = [{
        "provider": "prov1", "family": "fam1", "tokenizer": "tok1", "id": 1,
        "name": "model1", "api_model": "api1", "context_window": 5, "rate_limit": 10
    }]
    mock_registry_query.return_value = mock_db_response
    mock_process_db_response.return_value = [{
        "api": "prov1", "ai_families": [{
            "family": "fam1", "tokenizer": "tok1",
            "models": [{"id": 1, "name": "model1", "api_model": "api1", "context_window": 5, "rate_limit": 10}]
        }]
    }]

    result = test_handler._load_registry()

    mock_check_for_tables.assert_called_once()
    mock_registry_query.assert_called_once()
    mock_process_db_response.assert_called_once_with(mock_db_response)


@patch.object(SQLiteProviderHandler, "_check_for_tables")
@patch.object(SQLiteProviderHandler, "_registry_query")
@patch.object(SQLiteProviderHandler, "_process_db_response")
@patch("lorebinders.ai.ai_models.sqlite_model_handler.AIModelRegistry")
def test_load_registry_database_response_empty(mock_registry, mock_process_db_response, mock_registry_query, mock_check_for_tables, test_handler):
    mock_registry_query.return_value = []
    mock_process_db_response.return_value = []
    test_handler._load_registry()

    mock_check_for_tables.assert_called_once()
    mock_registry_query.assert_called_once()
    mock_process_db_response.assert_called_once()

@patch.object(SQLiteProviderHandler, "_check_for_tables")
@patch.object(SQLiteProviderHandler, "_registry_query")
@patch.object(SQLiteProviderHandler, "_process_db_response")
@patch("lorebinders.ai.ai_models.sqlite_model_handler.AIModelRegistry")
def test_load_registry_ai_model_registry_validation_fails(mock_registry, mock_process_db_response, mock_registry_query, mock_check_for_tables, test_handler):
    def raise_validation_error(*args, **kwargs):
        raise ValidationError.from_exception_data(
            title="Validation Error", line_errors=[]
        )

    mock_registry.model_validate.side_effect = raise_validation_error
    mock_registry_query.return_value = [{
        "provider": "test_provider", "family": "test_family", "tokenizer": "test_tokenizer", "id": 1,
        "name": "test_name", "api_model": "test_api_model", "context_window": 5, "rate_limit": "10"
    }]
    mock_process_db_response.return_value = [{
        "api": "prov1", "ai_families": [{
            "family": "fam1", "tokenizer": "tok1",
            "models": [{"id": 1, "name": "model1", "api_model": "api1", "context_window": 5, "rate_limit": "10"}]
        }]
    }]

    with pytest.raises(ValidationError):
        test_handler._load_registry()

def test_get_all_providers(test_handler, test_registry):
    test_handler._registry = test_registry
    result = test_handler.get_all_providers()
    assert len(result) == 3
    assert all(isinstance(x, APIProvider) for x in result)
    assert all(len(provider.ai_families) == 1 for provider in result)
    assert result[0].api == "OpenAI"
    assert result[1].api == "Anthropic"
    assert result[2].api == "Google"

@pytest.mark.parametrize(
    "provider",
    ["OpenAI", "Google", "Anthropic"],
)
def test_get_provider(provider, test_handler, test_registry):
    test_handler._registry = test_registry
    result = test_handler.get_provider(provider)
    assert result.api == provider

@patch.object(SQLiteProviderHandler, "_execute_query")
def test_add_provider(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry
    new_provider = APIProvider(api="NewAPI", ai_families=[])

    test_handler.add_provider(new_provider)

    assert new_provider in test_handler.registry.providers

    mock_execute_query.assert_called_once()

@patch.object(SQLiteProviderHandler, "_execute_query")
def test_delete_provider(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry

    test_handler.delete_provider("OpenAI")

    assert "OpenAI" not in [p.api for p in test_handler.registry.providers]

    mock_execute_query.assert_called_once()


def test_get_ai_family_success(test_handler, test_registry):
    test_handler._registry = test_registry

    result = test_handler.get_ai_family("OpenAI", "GPT")

    assert result.family == "GPT"
    assert result.tokenizer == "tiktoken"


@patch("lorebinders.ai.ai_models.sqlite_model_handler.logger")
def test_get_ai_family_failure(mock_logger, test_handler, test_registry):
    test_handler._registry = test_registry

    with pytest.raises(MissingModelFamilyError, match="No family BERT found for provider OpenAI"):
        test_handler.get_ai_family("OpenAI", "BERT")

    mock_logger.error.assert_called_once_with("No family BERT found for provider OpenAI")


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_add_ai_family(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry
    new_family = ModelFamily(family="BERT", tokenizer="bert_tokenizer", models=[])

    test_handler.add_ai_family("OpenAI", new_family)

    provider = test_handler.get_provider("OpenAI")
    assert new_family in provider.ai_families

    mock_execute_query.assert_called_once()


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_delete_ai_family(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry

    test_handler.delete_ai_family("OpenAI", "GPT")

    provider = test_handler.get_provider("OpenAI")
    assert "GPT" not in [f.family for f in provider.ai_families]

    mock_execute_query.assert_called_once()


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_add_model(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry
    new_model = Model(name="BERT-Base", api_model="bert-base", context_window=512, rate_limit=100)

    test_handler.add_model("OpenAI", "GPT", new_model)

    family = test_handler.get_ai_family("OpenAI", "GPT")
    assert new_model in family.models

    mock_execute_query.assert_called()


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_replace_model(mock_execute_query, test_handler, test_registry):
    Model._id_counter = 0
    test_handler._registry = test_registry
    updated_model = Model(name="GPT-4.1", api_model="gpt-4.1", context_window=9000, rate_limit=300, id=2)

    test_handler.replace_model(updated_model, 2, "GPT", "OpenAI")

    family = test_handler.get_ai_family("OpenAI", "GPT")
    assert updated_model in family.models

    mock_execute_query.assert_called_once()


@patch.object(SQLiteProviderHandler, "_execute_query")
def test_delete_model(mock_execute_query, test_handler, test_registry):
    test_handler._registry = test_registry

    test_handler.delete_model("OpenAI", "GPT", 2)

    family = test_handler.get_ai_family("OpenAI", "GPT")
    assert all(model.id != 2 for model in family.models)

    mock_execute_query.assert_called_once()


def test_get_model_attr(test_handler):
    model = Model(name="GPT-4", api_model="gpt-4", context_window=8192, rate_limit=200, id=1)

    result = test_handler.get_model_attr(model)

    assert result == ("GPT-4", "gpt-4", 8192, 200, 1)
