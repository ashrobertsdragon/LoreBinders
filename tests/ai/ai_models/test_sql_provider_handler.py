import os
import sqlite3
import shutil
import tempfile
from unittest.mock import patch, MagicMock

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
        yield mock

@pytest.fixture
def mock_os_path():
    with patch("lorebinders.ai.ai_models.sqlite_model_handler.os.path") as mock:
        mock.join.side_effect = os.path.join
        yield mock

@pytest.fixture
def mock_initialize_database():
    with patch.object(SQLiteProviderHandler, "_initialize_database") as mock:
        yield mock

@pytest.fixture
def mock_sqlite():
    with patch("lorebinders.ai.ai_models.sqlite_model_handler.SQLite") as mock:
        yield mock

@pytest.fixture
def mock_handler():
    handler = MagicMock(spec=SQLiteProviderHandler)
    handler.db = "/path/to/mock.db"
    return handler

def test_successful_operation(mock_sqlite3):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor

    with SQLite("test.db") as cursor:
        assert cursor == mock_cursor

    mock_sqlite3.connect.assert_called_once_with("test.db")
    mock_connection.commit.assert_called_once()
    mock_connection.close.assert_called_once()

def test_database_operation_error(mock_sqlite3):
    mock_sqlite3.connect.side_effect = sqlite3.Error("Database error")

    with pytest.raises(DatabaseOperationError):
        with SQLite("test.db"):
            pass

def test_exception_in_context(mock_sqlite3):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor

    with pytest.raises(ValueError):
        with SQLite("test.db") as cursor:
            raise ValueError("Test exception")

    mock_connection.rollback.assert_called_once()
    mock_connection.close.assert_called_once()

def test_row_factory_set(mock_sqlite3):
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection

    with SQLite("test.db"):
        pass

    assert mock_connection.row_factory == sqlite3.Row

def test_connection_closed_on_success(mock_sqlite3):
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection

    with SQLite("test.db"):
        pass

    mock_connection.close.assert_called_once()

def test_connection_closed_on_exception(mock_sqlite3):
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection

    with pytest.raises(ValueError):
        with SQLite("test.db"):
            raise ValueError("Test exception")

    mock_connection.close.assert_called_once()

def test_init_with_default_filename(mock_os_path, mock_initialize_database):
    schema_directory = "/path/to/schema"
    handler = SQLiteProviderHandler(schema_directory)

    mock_os_path.join.assert_called_once_with(schema_directory, "ai_models.db")
    assert handler.db == os.path.join(schema_directory, "ai_models.db")
    assert handler._registry is None
    mock_initialize_database.assert_called_once()

def test_init_with_custom_filename(mock_os_path, mock_initialize_database):
    schema_directory = "/path/to/schema"
    custom_filename = "custom.db"
    handler = SQLiteProviderHandler(schema_directory, schema_filename=custom_filename)

    mock_os_path.join.assert_called_once_with(schema_directory, custom_filename)
    assert handler.db == os.path.join(schema_directory, custom_filename)
    assert handler._registry is None
    mock_initialize_database.assert_called_once()

def test_init_with_database_operation_error(mock_os_path, mock_initialize_database):
    schema_directory = "/path/to/schema"
    mock_initialize_database.side_effect = DatabaseOperationError("Test error")

    with patch("lorebinders.ai.ai_models.sqlite_model_handler.logger") as mock_logger:
        handler = SQLiteProviderHandler(schema_directory)

        mock_logger.exception.assert_called_once()
        assert "Failed to initialize database" in mock_logger.exception.call_args[0][0]

def test_init_with_other_exception(mock_os_path, mock_initialize_database):
    schema_directory = "/path/to/schema"
    mock_initialize_database.side_effect = ValueError("Unexpected error")

    with pytest.raises(ValueError):
        SQLiteProviderHandler(schema_directory)

def test_initialize_database_success(mock_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor

    SQLiteProviderHandler._initialize_database(mock_handler)

    mock_sqlite.assert_called_once_with(mock_handler.db)
    assert mock_cursor.execute.call_count == 3

    # Check if the correct SQL statements are executed
    calls = mock_cursor.execute.call_args_list
    assert "CREATE TABLE IF NOT EXISTS providers" in calls[0][0][0]
    assert "CREATE TABLE IF NOT EXISTS ai_families" in calls[1][0][0]
    assert "CREATE TABLE IF NOT EXISTS models" in calls[2][0][0]

def test_initialize_database_sqlite_error(mock_handler, mock_sqlite):
    mock_sqlite.side_effect = DatabaseOperationError("SQLite error")

    with pytest.raises(DatabaseOperationError):
        SQLiteProviderHandler._initialize_database(mock_handler)

def test_initialize_database_execution_error(mock_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Execution error")
    mock_sqlite.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception):
        SQLiteProviderHandler._initialize_database(mock_handler)

@patch("lorebinders.ai.ai_models.sqlite_model_handler.logger")
def test_initialize_database_logs_success(mock_logger, mock_handler, mock_sqlite):
    mock_cursor = MagicMock()
    mock_sqlite.return_value.__enter__.return_value = mock_cursor

    SQLiteProviderHandler._initialize_database(mock_handler)

    mock_logger.info.assert_called_once_with("Database initialized")

@patch("lorebinders.ai.ai_models.sqlite_model_handler.logger")
def test_initialize_database_logs_error(mock_logger, mock_handler, mock_sqlite):
    mock_sqlite.side_effect = DatabaseOperationError("SQLite error")

    with pytest.raises(DatabaseOperationError):
        SQLiteProviderHandler._initialize_database(mock_handler)

    mock_logger.exception.assert_not_called()
