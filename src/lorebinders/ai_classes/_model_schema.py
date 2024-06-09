from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    model: str
    context_window: int


class Models(BaseModel):
    model1: Model
    model2: Model
    model3: Optional[Model] = None


class AIModels(BaseModel):
    provider: str
    models: Models
