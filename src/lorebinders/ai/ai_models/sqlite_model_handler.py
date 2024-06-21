import sqlite3
from typing import List, Optional

from _managers import AIProviderManager
from _types import AIModelRegistry, APIProvider, Model, ModelFamily
from ai.exceptions import MissingModelFamilyError


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
        self._registry: Optional[dict] = None
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
                    family_name TEXT NOT NULL,
                    PRIMARY KEY(id, family_name),
                    FOREIGN KEY(family_name) REFERENCES model_families(family)
                )
            """)

    def _execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> list:
        with SQLite(self.db) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def _load_registry(self) -> AIModelRegistry:
        with SQLite(self.db) as cursor:
            providers = cursor.execute("SELECT name FROM providers").fetchall()
            model_families = cursor.execute(
                "SELECT family, provider_name FROM model_families"
            ).fetchall()
            models = cursor.execute("""
                SELECT (
                    id,
                    name,
                    context_window,
                    rate_limit,
                    tokenizer,
                    family_name
                )
                FROM models
            """).fetchall()
        registry_data = {"providers": []}
        for provider in providers:
            provider_data = {"name": provider["name"], "model_families": []}
            for family in model_families:
                if family["provider_id"] == provider["id"]:
                    family_data = {"family": family["family"], "models": []}
                    for model in models:
                        if model["family_id"] == family["id"]:
                            family_data["models"].append({
                                "id": model["id"],
                                "name": model["name"],
                                "context_window": model["context_window"],
                                "rate_limit": model["rate_limit"],
                                "tokenizer": model["tokenizer"],
                            })
                    provider_data["model_families"].append(family_data)
            registry_data["providers"].append(provider_data)

        return AIModelRegistry.model_validate(registry_data)

    def get_all_providers(self) -> List[APIProvider]:
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
            "INSERT INTO model_families (family, provider_name) VALUES (?, ?)",
            (model_family.family, provider),
        )
        models = model_family.models
        for model in models:
            self.add_model(provider, model_family.name, model)

    def delete_model_family(self, provider: str, family: str) -> None:
        api_provider = self.get_provider(provider)
        api_provider.model_families = [
            f for f in provider.model_families if f.name != family
        ]
        self._execute_query(
            "DELETE FROM model_families WHERE name = ? "
            "AND provider_name = ?",
            (family, provider),
        )

    def add_model(self, provider: str, family: str, model: Model) -> None:
        family = self.get_model_family(provider, family)
        family.models.append(model)
        name, context_window, rate_limit, tokenizer, id = self.get_model_attr(
            model
        )
        self._execute_query(
            """
            INSERT INTO models (
                id, name, context_window, rate_limit, tokenizer, family_name
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id, name, context_window, rate_limit, tokenizer),
        )

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        model_family = self.get_model_family(provider, family)
        model.id = model_id
        model_family.models = [
            model if m.id != model_id else m for m in model_family.models
        ]
        name, context_window, rate_limit, tokenizer, id = self.get_model_attr(
            model
        )
        self._execute_query(
            """
            UPDATE models SET (
                name = ?, context_window = ?, rate_limit = ?, tokenizer = ?
            ) WHERE id = ? AND family_name = ?
            """,
            (name, context_window, rate_limit, tokenizer, id, family),
        )

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        family = self.get_model_family(provider, family)
        family.models = [m for m in family.models if m.id != model_id]
        self._execute_query(
            "DELETE FROM models WHERE id = ? AND family_name = ?",
            (model_id, family),
        )

    @staticmethod
    def get_model_attr(model: Model):
        name = model.name
        context_window = model.context_window
        rate_limit = model.rate_limit
        tokenizer = model.tokenizer
        model_id = model.id
        return name, context_window, rate_limit, tokenizer, model_id
