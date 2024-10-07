from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import cast

from loguru import logger

from lorebinders._decorators import log_db_error
from lorebinders.ai.ai_models._model_schema import AIModelRegistry
from lorebinders.ai.ai_models.sql_provider_handler import SQLProviderHandler
from lorebinders.ai.exceptions import DatabaseOperationError


class SQLite:
    def __init__(self, file: Path) -> None:
        self.file = file

    def __enter__(self):
        try:
            self.connection = sqlite3.connect(self.file)
            self.connection.row_factory = sqlite3.Row
            return self.connection.cursor()
        except sqlite3.Error as e:
            logger.error(e)
            raise DatabaseOperationError from e

    def __exit__(self, type, value, traceback):
        if type is not None:
            self.connection.rollback()
            logger.error(f"An error occurred: {value}")
        else:
            self.connection.commit()
        self.connection.close()


class SQLiteProviderHandler(SQLProviderHandler):
    """SQLite database handler for AI model data."""

    query_templates = {
        "delete": {
            "providers": "DELETE FROM providers WHERE api = ?",
            "ai_families": "DELETE FROM ai_families WHERE "
            "family = ? AND provider_api = ?",
            "models": "DELETE FROM models WHERE id = ? AND family = ?",
        },
        "insert": {
            "providers": "INSERT INTO providers (api) VALUES (?)",
            "ai_families": "INSERT INTO ai_families "
            "(family, tokenizer, provider_api) VALUES (?, ?, ?)",
            "models": "INSERT INTO models "
            "(id, name, api_model, context_window, rate_limit, family) VALUES "
            "(?, ?, ?, ?, ?, ?)",
        },
        "update": {
            "models": """
            UPDATE models SET
                name = ?,
                api_model = ?,
                context_window = ?,
                rate_limit = ?
            WHERE id = ? AND family = ?
            """
        },
    }

    def __init__(self, schema_directory: str, schema_filename="ai_models.db"):
        self.db = Path(schema_directory, schema_filename)
        self._registry: AIModelRegistry | None = None

    @log_db_error
    def _create_tables(self):
        with SQLite(self.db) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family TEXT NOT NULL,
                    tokenizer TEXT NOT NULL,
                    provider_api TEXT NOT NULL,
                    FOREIGN KEY(provider_api) REFERENCES providers(api)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    api_model TEXT NOT NULL,
                    context_window INTEGER NOT NULL,
                    rate_limit INTEGER NOT NULL,
                    max_output_tokens INTEGER NOT NULL,
                    generation TEXT NOT NULL,
                    family TEXT NOT NULL,
                    PRIMARY KEY(id, family),
                    FOREIGN KEY(family) REFERENCES ai_families(family)
                )
            """)
        logger.info("Database initialized")

    @log_db_error
    def _execute_query(self, query: str, params: tuple | None = None) -> list:
        with SQLite(self.db) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def _query_db(self, action: str, table: str, params: tuple) -> list:
        query = self._form_query(action, table)
        return self._execute_query(query, params)

    def _process_db_response(self, data: list[dict]) -> list[dict]:
        registry: list[dict] = []
        for row in data:
            provider_api: str = row["api"]
            family: str = row["family"]
            provider: dict[str, str | list[dict]] = next(
                (p for p in registry if p["api"] == provider_api),
                {"api": provider_api, "ai_families": []},
            )
            if provider not in registry:
                registry.append(provider)
            ai_families = cast(list, provider["ai_families"])
            ai_family: dict[str, str | int | list[dict]] = next(
                (f for f in ai_families if f["family"] == family),
                {
                    "family": family,
                    "tokenizer": row["tokenizer"],
                    "models": [],
                },
            )
            if ai_family not in ai_families:
                ai_families.append(ai_family)
            models = cast(list, ai_family["models"])
            model_data: dict[str, str | int] = {
                "id": row["id"],
                "name": row["name"],
                "api_model": row["api_model"],
                "context_window": row["context_window"],
                "rate_limit": row["rate_limit"],
                "max_output_tokens": row["max_output_tokens"],
                "generation": row["generation"],
            }
            models.append(model_data)
            ai_family["models"] = models
            provider["ai_families"] = ai_families
        return registry

    def _check_for_tables(self) -> None:
        check_table_query = """
            SELECT name FROM sqlite_master
            WHERE type="table"
        """
        existing_tables = self._execute_query(check_table_query)
        if len(existing_tables) < 3:
            self._create_tables()

    def _registry_query(self) -> list[dict]:
        """Returns the list of AI models in the database"""
        query = """
            SELECT
                p.api as api,
                af.provider_api,
                af.family as family,
                af.tokenizer,
                m.id,
                m.name,
                m.api_model,
                m.context_window,
                m.rate_limit,
                m.max_output_tokens,
                m.generation,
                m.family
            FROM providers p
            JOIN ai_families af
            ON p.api = af.provider_api
            JOIN models m
            ON m.family = family
            """
        return self._execute_query(query)

    def _load_registry(self) -> AIModelRegistry:
        self._check_for_tables()
        db_response = self._registry_query()
        registry_data = self._process_db_response(db_response)
        return AIModelRegistry(providers=registry_data)
