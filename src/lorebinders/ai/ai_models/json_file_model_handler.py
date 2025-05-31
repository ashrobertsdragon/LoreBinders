from __future__ import annotations

from json import JSONDecodeError
from pathlib import Path

from loguru import logger

from lorebinders._managers import AIProviderManager
from lorebinders.ai.ai_models._model_schema import (
    AIModelRegistry,
    APIProvider,
    Model,
    ModelFamily,
)
from lorebinders.ai.exceptions import (
    MissingAIProviderError,
    MissingModelError,
    MissingModelFamilyError,
)
from lorebinders.file_handling import read_json_file, write_json_file


class JSONFileProviderHandler(AIProviderManager):
    """JSON file-based AI provider handler."""

    def __init__(
        self, schema_directory: str, schema_filename: str = "ai_models.json"
    ) -> None:
        """Initialize the JSON file provider handler.

        Args:
            schema_directory: Directory containing the schema file.
            schema_filename: Name of the schema file.
        """
        self.schema_path = Path(schema_directory, schema_filename)

        self._registry: AIModelRegistry | None = None

    @property
    def registry(self) -> AIModelRegistry:
        """Get or load the AI model registry.

        Returns:
            The AI model registry.
        """
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    def _load_registry(self) -> AIModelRegistry:
        try:
            data = read_json_file(self.schema_path)
            return AIModelRegistry.model_validate(data)
        except JSONDecodeError as e:
            logger.error(
                f"Failed to load registry from {self.schema_path}: {str(e)}"
            )
            raise JSONDecodeError(e.msg, e.doc, e.pos) from e

    def get_all_providers(self) -> list[APIProvider]:
        """Get all API providers from the registry.

        Returns:
            List of all API providers.
        """
        return self.registry.providers

    def get_provider(self, provider: str) -> APIProvider:
        """Get a specific API provider by name.

        Args:
            provider: Name of the provider to retrieve.

        Returns:
            The requested API provider.

        Raises:
            MissingAIProviderError: If the provider is not found.
        """
        try:
            return self.registry.get_provider(provider)
        except MissingAIProviderError:
            logger.warning(f"Provider not found: {provider}")
            raise

    def add_provider(self, provider: APIProvider) -> None:
        """Add a new API provider to the registry.

        Args:
            provider: API provider to add.
        """
        try:
            self.registry.providers.append(provider)
            self._write_registry_to_file()
        except Exception as e:
            logger.error(f"Failed to add provider {provider.api}: {str(e)}")
            raise

    def delete_provider(self, provider: str) -> None:
        """Delete an API provider from the registry.

        Args:
            provider: Name of the provider to delete.
        """
        original_count = len(self.registry.providers)
        self.registry.providers = [
            p for p in self.registry.providers if p.api != provider
        ]
        if len(self.registry.providers) == original_count:
            logger.warning(f"Provider not found for deletion: {provider}")
        else:
            self._write_registry_to_file()

    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        """Get a model family from a provider.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.

        Returns:
            The requested model family.

        Raises:
            MissingModelFamilyError: If family not found for provider.
        """
        api_provider = self.get_provider(provider)
        if ai_family := api_provider.get_ai_family(family):
            return ai_family
        missing_model_error_msg = (
            f"No model family {family} found for provider {provider}"
        )
        logger.error(missing_model_error_msg)
        raise MissingModelFamilyError(missing_model_error_msg)

    def add_ai_family(self, provider: str, ai_family: ModelFamily) -> None:
        """Add a model family to a provider.

        Args:
            provider: Name of the API provider.
            ai_family: Model family to add.
        """
        api_provider = self.get_provider(provider)
        api_provider.ai_families.append(ai_family)
        self._write_registry_to_file()

    def delete_ai_family(self, provider: str, family: str) -> None:
        """Delete a model family from a provider.

        Args:
            provider: Name of the API provider.
            family: Name of the model family to delete.
        """
        api_provider = self.get_provider(provider)
        original_count = len(api_provider.ai_families)
        api_provider.ai_families = [
            f for f in api_provider.ai_families if f.family != family
        ]
        if len(api_provider.ai_families) == original_count:
            logger.warning(f"Family not found for deletion: {family}")
        else:
            self._write_registry_to_file()

    def add_model(self, provider: str, family: str, model: Model) -> None:
        """Add a model to a provider's family.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.
            model: Model to add.
        """
        ai_family = self.get_ai_family(provider, family)
        ai_family.models.append(model)
        self._write_registry_to_file()

    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        """Replace an existing model with a new one.

        Args:
            model: New model to replace with.
            model_id: ID of the model to replace.
            family: Name of the model family.
            provider: Name of the API provider.

        Raises:
            MissingModelError: If the model to replace is not found.
        """
        ai_family = self.get_ai_family(provider, family)
        original_models = ai_family.models.copy()
        model.id = model_id
        ai_family.models = [
            model if m.id == model_id else m for m in ai_family.models
        ]
        if ai_family.models == original_models:
            missing_model_error_msg = (
                f"Model not found for replacement: {model_id} for {family}"
            )
            logger.warning(missing_model_error_msg)
            raise MissingModelError(missing_model_error_msg)
        self._write_registry_to_file()

    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        """Delete a model from a provider's family.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.
            model_id: ID of the model to delete.
        """
        ai_family = self.get_ai_family(provider, family)
        ai_family.models = [m for m in ai_family.models if m.id != model_id]
        self._write_registry_to_file()

    def _write_registry_to_file(self) -> None:
        try:
            json_data = self.registry.model_dump()
            write_json_file(json_data, self.schema_path)
        except Exception as e:
            logger.error(
                f"Could not write to file {self.schema_path}: {str(e)}"
            )
            raise
