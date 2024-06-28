from __future__ import annotations

import sqlite3

from ._model_schema import AIModelRegistry, APIProvider, Model, ModelFamily

from lorebinders._managers import AIProviderManager
from lorebinders.ai.exceptions import MissingModelFamilyError


class SQLite:
    def __init__(self, file="ai_models.db"):
        self.file = file

    def __enter__(self):
        self.connection = sqlite3.connect(self.file)
        self.connection.row_factory = sqlite3.Row
        return self.connection.cursor()

    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()


class SQLiteProviderHandler(AIProviderManager):
    def __init__(self) -> None:
        self.db: str = "ai_models.db"
        self._registry: AIModelRegistry | None = None
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    FOREIGN KEY(provider_name) REFERENCES providers(name)
                )
            """)
            cursor.execute("""
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
                p.name as provider,
                mf.provider_name,
                mf.family as family,
                m.id,
                m.name
                m.context_window,
                m.rate_limit,
                m.tokenizer,
                m.family
            FROM providers p
            JOIN model_families mf
            ON p.id = mf.provider_id
            JOIN models m
            ON m.family = family
            """
        return self._execute_query(query)

    def _process_db_response(self, data: list[dict]) -> list[dict]:
        registry: list[dict] = []
        provider = {}
        for row in data:
            provider_name = row["provider"]
            family = row["family"]
            if provider_name not in provider:
                provider = {
                    "name": provider_name,
                    "model_families": [],
                }
            current_family = None
            if family != current_family:
                current_family = family
                model_family = {"family": family, "models": []}
                provider["model_families"].append(model_family)
            model_data = {
                "id": row["id"],
                "name": row["name"],
                "context_window": row["context_window"],
                "rate_limit": row["rate_limit"],
                "tokenizer": row["tokenizer"],
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
            "INSERT INTO providers (name) VALUES (?)", (provider.name,)
        )
        for family in provider.model_families:
            self.add_model_family(provider.name, family)

    def delete_provider(self, provider: str) -> None:
        self.registry.providers = [
            p for p in self.registry.providers if p.name != provider
        ]
        self._execute_query(
            "DELETE FROM providers WHERE name = ?", (provider,)
        )

    def get_model_family(self, provider: str, family: str) -> ModelFamily:
        api_provider = self.get_provider(provider)
        if model_family := api_provider.get_model_family(family):
            return model_family
        raise MissingModelFamilyError(
            f"No family {family} found for provider {provider}"
        )

    def add_model_family(
        self, provider: str, model_family: ModelFamily
    ) -> None:
        api_provider = self.get_provider(provider)
        api_provider.model_families.append(model_family)
        self._execute_query(
            """
            INSERT INTO model_families
            (family, tokenizer, provider_name)
            VALUES (?, ?, ?)
            """,
            (model_family.family, model_family.tokenizer, provider),
        )
        models = model_family.models
        for model in models:
            self.add_model(provider, model_family.family, model)

    def delete_model_family(self, provider: str, family: str) -> None:
        api_provider = self.get_provider(provider)
        api_provider.model_families = [
            f for f in api_provider.model_families if f.family != family
        ]
        self._execute_query(
            "DELETE FROM model_families WHERE name = ? "
            "AND provider_name = ?",
            (family, provider),
        )

    def add_model(self, provider: str, family: str, model: Model) -> None:
        model_family = self.get_model_family(provider, family)
        model_family.models.append(model)
        name, context_window, rate_limit, id = self.get_model_attr(model)
        self._execute_query(
            """
            INSERT INTO models (
                id, name, context_window, rate_limit, family
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id, name, context_window, rate_limit, family),
        )

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        model_family = self.get_model_family(provider, family)
        model.id = model_id
        model_family.models = [
            model if m.id != model_id else m for m in model_family.models
        ]
        name, context_window, rate_limit, id = self.get_model_attr(model)
        self._execute_query(
            """
            UPDATE models SET (
                name = ?, context_window = ?, rate_limit = ?, tokenizer = ?
            ) WHERE id = ? AND family = ?
            """,
            (name, context_window, rate_limit, id, family),
        )

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        model_family = self.get_model_family(provider, family)
        model_family.models = [
            m for m in model_family.models if m.id != model_id
        ]
        self._execute_query(
            "DELETE FROM models WHERE id = ? AND family = ?",
            (model_id, family),
        )

    @staticmethod
    def get_model_attr(model: Model):
        name = model.name
        context_window = model.context_window
        rate_limit = model.rate_limit
        model_id = model.id
        return name, context_window, rate_limit, model_id
