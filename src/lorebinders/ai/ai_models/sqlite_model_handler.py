from __future__ import annotations

import os
import sqlite3

from ._model_schema import AIModelRegistry, APIProvider, Model, ModelFamily

from lorebinders._managers import AIProviderManager
from lorebinders.ai.exceptions import MissingModelFamilyError


class SQLite:
    def __init__(self, file: str) -> None:
        self.file = file

    def __enter__(self):
        self.connection = sqlite3.connect(self.file)
        self.connection.row_factory = sqlite3.Row
        return self.connection.cursor()

    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()


class SQLiteProviderHandler(AIProviderManager):
    def __init__(self, schema_directory, schema_filename="ai_models.db"):
        self.db = os.path.join(schema_directory, schema_filename)
        self._registry = None
        self._initialize_database()

    def _initialize_database(self):
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
                    context_window INTEGER NOT NULL,
                    rate_limit INTEGER NOT NULL,
                    family TEXT NOT NULL,
                    PRIMARY KEY(id, family_name),
                    FOREIGN KEY(family_name) REFERENCES ai_families(family)
                )
            """)

    def _execute_query(self, query: str, params: tuple | None = None) -> list:
        with SQLite(self.db) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def _registry_query(self) -> list[dict]:
        query = """
            SELECT
                p.api as provider,
                af.provider_api,
                af.family as family,
                af.tokenizer,
                m.id,
                m.name
                m.api_str,
                m.context_window,
                m.rate_limit,
                m.family
            FROM providers p
            JOIN ai_families af
            ON p.api = af.provider_api
            JOIN models m
            ON m.family = family
            """
        return self._execute_query(query)

    def _process_db_response(self, data: list[dict]) -> list[dict]:
        registry: list[dict] = []
        provider = {}
        for row in data:
            provider_api = row["provider"]
            family = row["family"]
            if provider_api not in provider:
                provider = {
                    "api": provider_api,
                    "ai_families": [],
                }
            current_family = None
            if family != current_family:
                current_family = family
                ai_family = {
                    "family": family,
                    "tokenizer": row["tokenizer"],
                    "models": [],
                }
                provider["ai_families"].append(ai_family)
            model_data = {
                "id": row["id"],
                "name": row["name"],
                "api_str": row["api_str"],
                "context_window": row["context_window"],
                "rate_limit": row["rate_limit"],
            }
            current_family["models"].append(model_data)
            registry.append(provider)
        return registry

    def _load_registry(self) -> AIModelRegistry:
        db_response = self._registry_query()
        registry_data = self._process_db_response(db_response)
        return AIModelRegistry.model_validate(registry_data)

    def get_all_providers(self) -> list[APIProvider]:
        return self.registry.providers

    def get_provider(self, provider: str) -> APIProvider:
        return self.registry.get_provider(provider)

    def add_provider(self, provider: APIProvider) -> None:
        self.registry.providers.append(provider)
        self._execute_query(
            "INSERT INTO providers (api) VALUES (?)", (provider.api,)
        )
        for family in provider.ai_families:
            self.add_ai_family(provider.api, family)

    def delete_provider(self, provider: str) -> None:
        self.registry.providers = [
            p for p in self.registry.providers if p.api != provider
        ]
        self._execute_query("DELETE FROM providers WHERE api = ?", (provider,))

    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        api_provider = self.get_provider(provider)
        if ai_family := api_provider.get_ai_family(family):
            return ai_family
        raise MissingModelFamilyError(
            f"No family {family} found for provider {provider}"
        )

    def add_ai_family(self, provider: str, ai_family: ModelFamily) -> None:
        api_provider = self.get_provider(provider)
        api_provider.ai_families.append(ai_family)
        self._execute_query(
            """
            INSERT INTO ai_families
            (family, tokenizer, provider_api)
            VALUES (?, ?, ?)
            """,
            (ai_family.family, ai_family.tokenizer, provider),
        )
        models = ai_family.models
        for model in models:
            self.add_model(provider, ai_family.family, model)

    def delete_ai_family(self, provider: str, family: str) -> None:
        api_provider = self.get_provider(provider)
        api_provider.ai_families = [
            f for f in api_provider.ai_families if f.family != family
        ]
        self._execute_query(
            "DELETE FROM ai_families WHERE family = ? " "AND provider_api = ?",
            (family, provider),
        )

    def add_model(self, provider: str, family: str, model: Model) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models.append(model)
        name, api_str, context_window, rate_limit, id = self.get_model_attr(
            model
        )
        self._execute_query(
            """
            INSERT INTO models (
                id, name, api_str, context_window, rate_limit, family
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (id, api_str, name, context_window, rate_limit, family),
        )

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        ai_family = self.get_ai_family(provider, family)
        model.id = model_id
        ai_family.models = [
            model if m.id != model_id else m for m in ai_family.models
        ]
        name, api_str, context_window, rate_limit, id = self.get_model_attr(
            model
        )
        self._execute_query(
            """
            UPDATE models SET (
                name = ?,
                api_str = ?,
                context_window = ?,
                rate_limit = ?,
            ) WHERE id = ? AND family = ?
            """,
            (name, api_str, context_window, rate_limit, id, family),
        )

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models = [m for m in ai_family.models if m.id != model_id]
        self._execute_query(
            "DELETE FROM models WHERE id = ? AND family = ?",
            (model_id, family),
        )

    @staticmethod
    def get_model_attr(model: Model):
        name = model.name
        api_str = model.api_str
        context_window = model.context_window
        rate_limit = model.rate_limit
        model_id = model.id
        return name, api_str, context_window, rate_limit, model_id
