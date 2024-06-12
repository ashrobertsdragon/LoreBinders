from typing import Any, Dict, List

from pydantic import BaseModel, Field, root_validator


class Model(BaseModel):
    id: int
    model: str
    context_window: int
    rate_limit: int
    tokenizer: str


class Models(BaseModel):
    models: List[Model] = Field(default_factory=list)

    _id_counter = 0

    @root_validator(pre=True)
    def set_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        models = values.get("models", [])
        for model in models:
            if "id" not in model:
                cls._id_counter += 1
                model["id"] = cls._id_counter
        return values

    def get_model_by_id(self, model_id: int) -> Model:
        while model_id > 0:
            for model in self.models:
                if model.id == model_id:
                    return model
            model_id -= 1
        raise ValueError("No model found.")


class AIModels(BaseModel):
    provider: str
    models: Models
