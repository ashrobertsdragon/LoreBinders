from typing import Any, Dict, List

from pydantic import BaseModel, Field, root_validator


class Model(BaseModel):
    id: int = Field(init=False)
    name: str
    context_window: int
    rate_limit: int


class ModelFamily(BaseModel):
    family: str
    tokenizer: str
    models: List[Model] = Field(default_factory=list)

    _id_counter = 0

    @root_validator(pre=True)
    def set_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        models = values.get("models", [])
        for model in models:
            cls._id_counter += 1
            if "id" not in model:
                model["id"] = cls._id_counter
        return values

    def get_model_by_id(self, model_id: int) -> Model:
        while model_id > 0:
            for model in self.models:
                if model.id == model_id:
                    return model
            model_id -= 1
        return self.models[0]


class APIProvider(BaseModel):
    name: str
    model_families: List[ModelFamily] = Field(default_factory=list)

    def get_model_family(self, family: str) -> ModelFamily:
        return next(
            (
                model_family
                for model_family in self.model_families
                if model_family.family.lower() == family.lower()
            ),
            self.model_families[0],
        )


class AIModelRegistry(BaseModel):
    providers: List[APIProvider] = Field(default_factory=list)

    def get_provider(self, name: str) -> APIProvider:
        return next(
            (
                provider
                for provider in self.providers
                if provider.name.lower() == name.lower()
            ),
            self.providers[0],
        )
