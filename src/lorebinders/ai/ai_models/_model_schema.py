from typing import Any, Dict, List

from pydantic import BaseModel, Field, model_validator


class Model(BaseModel):
    id: int = Field(default_factory=lambda: Model._id_counter)
    name: str
    api_model: str
    context_window: int
    rate_limit: int
    absolute_max_tokens: int = Field(default_factory=lambda: 4096)

    _id_counter: int = 0

    @classmethod
    def _increment_counter(cls):
        cls._id_counter += 1
        return cls._id_counter

    def __str__(self) -> str:
        return self.name


class ModelFamily(BaseModel):
    family: str
    tokenizer: str
    models: List[Model] = Field(default_factory=list)

    def __str__(self) -> str:
        return self.family

    @model_validator(mode="before")
    @classmethod
    def set_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        models = values.get("models", [])
        for model in models:
            if isinstance(model, dict) and "id" not in model:
                model["id"] = Model._increment_counter()
        return values

    def get_model_by_id(self, model_id: int) -> Model:
        while model_id > 0:
            for model in self.models:
                if model.id == model_id:
                    return model
            model_id -= 1
        return self.models[0]


class APIProvider(BaseModel):
    api: str
    ai_families: List[ModelFamily] = Field(default_factory=list)

    def __str__(self) -> str:
        return self.api

    def get_ai_family(self, family: str) -> ModelFamily:
        """
        Retrieves the AI family that matches the given family name,
        case-insensitively.

        Args:
            family (str): The name of the AI family to retrieve.

        Returns:
            ModelFamily: The AI family that matches the given name, or the
            first AI family in the list if no match is found.
        """
        return next(
            (
                ai_family
                for ai_family in self.ai_families
                if ai_family.family.lower() == family.lower()
            ),
            self.ai_families[0],
        )


class AIModelRegistry(BaseModel):
    providers: List[APIProvider] = Field(default_factory=list)

    def get_provider(self, name: str) -> APIProvider:
        return next(
            (
                provider
                for provider in self.providers
                if provider.api.lower() == name.lower()
            ),
            self.providers[0],
        )
