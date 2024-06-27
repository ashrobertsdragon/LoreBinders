from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ai.ai_models._model_schema import (
    AIModelRegistry,
    APIProvider,
    Model,
    ModelFamily
)


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
    def read(self, model: str) -> dict:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def write(self, model: str, rate_limit_data: dict) -> None:
        raise NotImplementedError("Must be implemented in child class")


class AIProviderManager(ABC):
    _registry: Optional[AIModelRegistry] = None

    @property
    def registry(self) -> AIModelRegistry:
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    @abstractmethod
    def _load_registry(self) -> AIModelRegistry:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_all_providers(self) -> List[APIProvider]:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_provider(self, provider: str) -> APIProvider:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_provider(self, provider: APIProvider) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_provider(self, provider: str) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_model_family(self, provider: str, family: str) -> ModelFamily:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_model_family(
        self, provider: str, model_family: ModelFamily
    ) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_model_family(self, provider: str, family: str) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_model(self, provider: str, family: str, model: Model) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def replace_model(self, provider: str, family: str, model: Model) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        raise NotImplementedError("Must be implemented by child class")
