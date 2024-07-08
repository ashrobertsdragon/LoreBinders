from __future__ import annotations

from abc import ABC, abstractmethod

from lorebinders.ai.ai_models._model_schema import (
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
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> None:
        raise NotImplementedError("subclass must implement send_mail")

    @abstractmethod
    def error_email(self, error_msg: str) -> None:
        raise NotImplementedError("subclass must implement error_email")


class ErrorManager(ABC):
    def __init__(
        self, email_manager: EmailManager, unresolvable_errors: tuple
    ) -> None:
        self.email = email_manager
        self.unresolvable_errors = unresolvable_errors

    @abstractmethod
    def _extract_error_info(self, e: Exception) -> tuple[int, str]:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _is_unresolvable_error(
        self, e: Exception, error_code: int, error_message: str
    ) -> bool:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def handle_error(self, e: Exception, retry_count: int = 0) -> int:
        raise NotImplementedError("Must be implemented in child class")


class RateLimitManager(ABC):
    @abstractmethod
    def read(self, model: str) -> dict:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def write(self, model: str, rate_limit_data: dict) -> None:
        raise NotImplementedError("Must be implemented in child class")


class AIProviderManager(ABC):
    _registry: AIModelRegistry | None = None

    @property
    def registry(self) -> AIModelRegistry:
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    @abstractmethod
    def _load_registry(self) -> AIModelRegistry:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_all_providers(self) -> list[APIProvider]:
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
    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_ai_family(self, provider: str, model_family: ModelFamily) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_ai_family(self, provider: str, family: str) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_model(self, provider: str, family: str, model: Model) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        raise NotImplementedError("Must be implemented by child class")
