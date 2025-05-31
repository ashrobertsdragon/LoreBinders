from __future__ import annotations

from abc import ABC, abstractmethod

from lorebinders.ai.ai_models._model_schema import (
    AIModelRegistry,
    APIProvider,
    Model,
    ModelFamily,
)


class EmailManager(ABC):
    """Abstract base class for email management operations."""

    @abstractmethod
    def send_mail(
        self,
        user_email: str,
        attachment: tuple[str, str, str] | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Send an email to the specified user.

        Args:
            user_email: Recipient's email address.
            attachment: Optional tuple of (filename, content, content_type).
            error_msg: Optional error message to include.
        """
        raise NotImplementedError("subclass must implement send_mail")

    @abstractmethod
    def error_email(self, error_msg: str) -> None:
        """Send an error notification email.

        Args:
            error_msg: Error message to send.
        """
        raise NotImplementedError("subclass must implement error_email")


class ErrorManager(ABC):
    """Abstract base class for error handling and management."""

    def __init__(
        self, email_manager: EmailManager, unresolvable_errors: tuple
    ) -> None:
        """Initialize the error manager.

        Args:
            email_manager: Manager for sending error notifications.
            unresolvable_errors: Tuple of unresolvable error types.
        """
        self.email = email_manager
        self.unresolvable_errors = unresolvable_errors

    @abstractmethod
    def _extract_error_info(self, e: Exception) -> tuple[int, str]:
        """Extract error code and message from exception.

        Args:
            e: Exception to extract information from.

        Returns:
            Tuple of (error_code, error_message).
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _is_unresolvable_error(
        self, e: Exception, error_code: int, error_message: str
    ) -> bool:
        """Check if the error is unresolvable.

        Args:
            e: Original exception.
            error_code: Extracted error code.
            error_message: Extracted error message.

        Returns:
            True if error is unresolvable, False otherwise.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def handle_error(self, e: Exception, retry_count: int = 0) -> int:
        """Handle an error and determine retry behavior.

        Args:
            e: Exception to handle.
            retry_count: Current retry attempt count.

        Returns:
            Sleep time before retry, or -1 if unresolvable.
        """
        raise NotImplementedError("Must be implemented in child class")


class RateLimitManager(ABC):
    """Abstract base class for rate limit management."""

    @abstractmethod
    def read(self, model: str) -> dict:
        """Read rate limit data for a model.

        Args:
            model: Model name to read rate limit data for.

        Returns:
            Dictionary containing rate limit information.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def write(self, model: str, rate_limit_data: dict) -> None:
        """Write rate limit data for a model.

        Args:
            model: Model name to write rate limit data for.
            rate_limit_data: Rate limit information to store.
        """
        raise NotImplementedError("Must be implemented in child class")


class AIProviderManager(ABC):
    """Abstract base class for AI provider management operations."""

    _registry: AIModelRegistry | None = None

    @property
    def registry(self) -> AIModelRegistry:
        """Get the AI model registry, loading it if necessary.

        Returns:
            The AI model registry.
        """
        if not self._registry:
            self._registry = self._load_registry()
        return self._registry

    @abstractmethod
    def _load_registry(self) -> AIModelRegistry:
        """Load the AI model registry.

        Returns:
            The loaded AI model registry.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_all_providers(self) -> list[APIProvider]:
        """Get all API providers.

        Returns:
            List of all API providers.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_provider(self, provider: str) -> APIProvider:
        """Get a specific API provider.

        Args:
            provider: Name of the provider to retrieve.

        Returns:
            The requested API provider.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_provider(self, provider: APIProvider) -> None:
        """Add a new API provider.

        Args:
            provider: API provider to add.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_provider(self, provider: str) -> None:
        """Delete an API provider.

        Args:
            provider: Name of the provider to delete.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def get_ai_family(self, provider: str, family: str) -> ModelFamily:
        """Get a model family from a provider.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.

        Returns:
            The requested model family.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_ai_family(self, provider: str, model_family: ModelFamily) -> None:
        """Add a model family to a provider.

        Args:
            provider: Name of the API provider.
            model_family: Model family to add.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_ai_family(self, provider: str, family: str) -> None:
        """Delete a model family from a provider.

        Args:
            provider: Name of the API provider.
            family: Name of the model family to delete.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def add_model(self, provider: str, family: str, model: Model) -> None:
        """Add a model to a provider's family.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.
            model: Model to add.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def replace_model(
        self, model: Model, model_id: int, family: str, provider: str
    ) -> None:
        """Replace an existing model.

        Args:
            model: New model to replace with.
            model_id: ID of the model to replace.
            family: Name of the model family.
            provider: Name of the API provider.
        """
        raise NotImplementedError("Must be implemented by child class")

    @abstractmethod
    def delete_model(self, provider: str, family: str, model_id: int) -> None:
        """Delete a model from a provider's family.

        Args:
            provider: Name of the API provider.
            family: Name of the model family.
            model_id: ID of the model to delete.
        """
        raise NotImplementedError("Must be implemented by child class")
