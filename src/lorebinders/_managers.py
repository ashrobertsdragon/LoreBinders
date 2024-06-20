from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from _types import AIModels, Model


class EmailManager(ABC):
    @abstractmethod
    def send_mail(
        self,
        user_email: str,
        attachment: Optional[Tuple[str, str, str]] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        raise NotImplementedError("subclass must implement send_mail")

    @abstractmethod
    def error_email(self, error_msg: str) -> None:
        raise NotImplementedError("subclass must implement error_email")


class ErrorManager(ABC):
    @abstractmethod
    def kill_app(cls, e: Exception) -> None:
        raise NotImplementedError("subclass must implement kil_app")


class RateLimitManager(ABC):
    @abstractmethod
    def read(self, model_name: str) -> dict:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def write(self, model_name: str, rate_limit_data: dict) -> None:
        raise NotImplementedError("Must be implemented in child class")


class AIModelManager(ABC):
    @abstractmethod
    def get_all_models(self) -> List[AIModels]:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_provider(self, provider: str) -> AIModels:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_ai_model(self, ai_model: AIModels) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_model(self, model: Model, provider: str) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_ai_model(self, provider: str) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_model(self, model_id: int, provider: str) -> None:
        raise NotImplementedError("Must be implemented by child class")
