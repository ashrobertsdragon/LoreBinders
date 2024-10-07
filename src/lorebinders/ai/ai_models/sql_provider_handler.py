from abc import abstractmethod

from loguru import logger

from lorebinders._managers import AIProviderManager
from lorebinders.ai.ai_models._model_schema import (
    AIModelRegistry,
    APIProvider,
    Model,
    ModelFamily,
)
from lorebinders.ai.exceptions import MissingModelFamilyError


class SQLProviderHandler(AIProviderManager):
    """Abstract SQL database handler for AI model data."""

    query_templates: dict = {}  # Must be implemented in child class

    @property
    def registry(self) -> AIModelRegistry:
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    @abstractmethod
    def _load_registry(self) -> AIModelRegistry:
        "Must be implemented in child class"
        ...

    def _form_query(self, action: str, table: str) -> str:
        return self.query_templates[action][table]

    @abstractmethod
    def _query_db(self, action: str, table: str, params: tuple) -> list:
        """Must be implemented in child class"""
        ...

    @abstractmethod
    def _process_db_response(self, data: list[dict]) -> list[dict]:
        """Must be implemented in child class"""
        ...

    def get_all_providers(self) -> list[APIProvider]:
        return self.registry.providers

    def get_provider(self, provider: str) -> APIProvider:
        return self.registry.get_provider(provider)

    def add_provider(self, provider: APIProvider) -> None:
        self.registry.providers.append(provider)
        self._query_db("insert", "providers", (provider.api,))
        for family in provider.ai_families:
            self.add_ai_family(provider.api, family)

    def delete_provider(self, provider: str) -> None:
        self.registry.providers = [
            p for p in self.registry.providers if p.api != provider
        ]
        self._query_db("delete", "providers", (provider,))

    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        api_provider = self.get_provider(provider)

        if ai_family := api_provider.get_ai_family(family):
            if ai_family.family == family:
                return ai_family
        missing_family_error_msg = (
            f"No family {family} found for provider {provider}"
        )
        logger.error(missing_family_error_msg)
        raise MissingModelFamilyError(missing_family_error_msg)

    def add_ai_family(self, provider: str, ai_family: ModelFamily) -> None:
        api_provider = self.get_provider(provider)
        api_provider.ai_families.append(ai_family)
        self._query_db(
            "insert",
            "ai_families",
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
        self._query_db(
            "delete",
            "ai_families",
            (family, provider),
        )

    def add_model(self, provider: str, family: str, model: Model) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models.append(model)
        (
            name,
            api_model,
            context_window,
            rate_limit,
            max_output_tokens,
            generation,
            id,
        ) = self.get_model_attr(model)
        self._query_db(
            "insert",
            "models",
            (
                id,
                api_model,
                name,
                context_window,
                rate_limit,
                max_output_tokens,
                generation,
                family,
            ),
        )

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        ai_family = self.get_ai_family(provider, family)
        model.id = model_id
        ai_family.models = [
            model if m.id == model_id else m for m in ai_family.models
        ]
        name, api_model, context_window, rate_limit, id = self.get_model_attr(
            model
        )
        self._query_db(
            "update",
            "models SET",
            (name, api_model, context_window, rate_limit, id, family),
        )

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models = [m for m in ai_family.models if m.id != model_id]
        self._query_db(
            "delete",
            "models",
            (model_id, family),
        )

    @staticmethod
    def get_model_attr(model: Model):
        name = model.name
        api_model = model.api_model
        context_window = model.context_window
        rate_limit = model.rate_limit
        max_output_tokens = model.max_output_tokens
        generation: str = model.generation
        model_id = model.id
        return (
            name,
            api_model,
            context_window,
            rate_limit,
            max_output_tokens,
            generation,
            model_id,
        )
