from __future__ import annotations

import os

from ._model_schema import AIModelRegistry, APIProvider, Model, ModelFamily

from lorebinders._managers import AIProviderManager
from lorebinders.ai.exceptions import MissingModelFamilyError
from lorebinders.file_handling import read_json_file, write_json_file


class JSONFileProviderHandler(AIProviderManager):
    def __init__(
        self, schema_directory: str, schema_filename: str = "ai_models.json"
    ) -> None:
        self.schema_path = os.path.join(schema_directory, schema_filename)

        self._registry: AIModelRegistry | None = None

    @property
    def registry(self) -> AIModelRegistry:
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    def _load_registry(self) -> AIModelRegistry:
        data = read_json_file(self.schema_path)
        return AIModelRegistry.model_validate(data)

    def get_all_providers(self) -> list[APIProvider]:
        return self.registry.providers

    def get_provider(self, provider: str) -> APIProvider:
        return self.registry.get_provider(provider)

    def add_provider(self, provider: APIProvider) -> None:
        self.registry.providers.append(provider)
        self._write_registry_to_file()

    def delete_provider(self, provider: str) -> None:
        self.registry.providers = [
            p for p in self.registry.providers if p.api != provider
        ]
        self._write_registry_to_file()

    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        api_provider = self.get_provider(provider)
        if ai_family := api_provider.get_ai_family(family):
            return ai_family
        else:
            raise MissingModelFamilyError(
                f"No model family {family} found for provider {provider}"
            )

    def add_ai_family(self, provider: str, ai_family: ModelFamily) -> None:
        api_provider = self.get_provider(provider)
        api_provider.ai_families.append(ai_family)
        self._write_registry_to_file()

    def delete_ai_family(self, provider: str, family: str) -> None:
        api_provider = self.get_provider(provider)
        api_provider.ai_families = [
            f for f in api_provider.ai_families if f.family != family
        ]
        self._write_registry_to_file()

    def add_model(self, provider: str, family: str, model: Model) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models.append(model)
        self._write_registry_to_file()

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        ai_family = self.get_ai_family(provider, family)
        model.id = model_id
        ai_family.models = [
            model if m.id != model_id else m for m in ai_family.models
        ]
        self._write_registry_to_file()

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        ai_family = self.get_ai_family(provider, family)
        ai_family.models = [m for m in ai_family.models if m.id != model_id]
        self._write_registry_to_file()

    def _write_registry_to_file(self) -> None:
        json_data = self.registry.model_dump()
        write_json_file(json_data, self.schema_path)
