from typing import List

from _managers import AIModelManager
from _types import AIModels, Model
from file_handling import read_json_file, write_json_file
from lorebinders.ai.exceptions import MissingAIProviderError


class JSONFileModelHandler(AIModelManager):
    def __init__(self) -> None:
        self.model_file = "ai_models.json"
        self.all_models = self.get_all_models()

    def get_all_models(self) -> List[AIModels]:
        model_families = read_json_file(self.model_file)
        return [AIModels.model_validate(family) for family in model_families]

    def get_provider(self, provider: str) -> AIModels:
        if provider_instance := next(
            (
                instance
                for instance in self.all_models
                if instance.provider == provider
            ),
            None,
        ):
            return provider_instance
        else:
            raise MissingAIProviderError(f"No provider {provider} found")

    def add_ai_model(self, ai_model: AIModels) -> None:
        self.all_models.append(ai_model)
        self._write_models_to_file()

    def add_model(self, model: Model, provider: str) -> None:
        ai_model = self.get_provider(provider)
        ai_model.models.append(model)
        self._write_models_to_file()

    def delete_ai_model(self, provider: str) -> None:
        """Deletes an AI model family by its provider name."""
        self.all_models = [
            model for model in self.all_models if model.provider != provider
        ]
        self._write_models_to_file()

    def delete_model(self, model_id: int, provider: str) -> None:
        """Deletes a specific model by ID within an AI model family."""
        ai_model = self.get_provider(provider)
        ai_model.models = [
            model for model in ai_model.models if model.id != model_id
        ]
        self._write_models_to_file()

    def _write_models_to_file(self) -> None:
        """
        Helper method to write the current models to the JSON file.
        """
        json_models = [model.model_dump() for model in self.all_models]
        write_json_file(json_models, self.model_file)
