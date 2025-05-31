from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, ValidationError

from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.rate_limit import RateLimit

if TYPE_CHECKING:
    from lorebinders._managers import EmailManager, RateLimitManager
    from lorebinders._type_annotations import ChatCompletion, FinishReason
    from lorebinders.ai.ai_models._model_schema import Model


class Payload(BaseModel):
    """Pydantic model for API payload validation."""

    api_model: str
    role_script: str
    prompt: str
    temperature: float
    max_tokens: int


class AIManager(ABC):
    """Abstract base class for AI API management."""

    @abstractmethod
    def __init__(self, email_handler: EmailManager) -> None:
        """Initialize AI manager with email handler.

        This method provides a reference for child class implementation.

        Args:
            email_handler: Manager for sending error notifications.
        """
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )
        self.api_model: str | None = None

    @abstractmethod
    def _set_unresolvable_errors(self) -> tuple:
        """Set a tuple of errors that are unrecoverable in the API.

        This method must be implemented in the child class for specific API.

        Returns:
            Tuple of unresolvable error types.

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _count_tokens(self, text: str) -> int:
        """Count tokens using the tokenizer for the AI model.

        This method must be implemented in the child class for specific API
        implementations.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens in the text.

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]:
        """Create the message payload for the API call.

        This method must be implemented in the child class for specific API
        implementations.

        Args:
            role_script: System instruction for the AI.
            prompt: User prompt for the AI.
            assistant_message: Optional previous assistant message.

        Returns:
            Tuple of (messages list, input token count).

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """Make API calls to the AI engine.

        This method must be implemented in the child class for specific API
        implementations.

        Args:
            api_payload: Dictionary containing API parameters.
            json_response: Whether to expect JSON response format.
            retry_count: Current retry attempt count.
            assistant_message: Optional previous assistant message.

        Returns:
            The API response text.

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]:
        """Create a tuple from the response from the API call.

        This method must be implemented in the child class for specific API
        implementations.

        Args:
            response: The raw response from API.

        Returns:
            Tuple of (content, completion_tokens, finish_reason).

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def process_response(
        self,
        content_tuple: tuple[str, int, FinishReason],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        assistant_message: str | None = None,
    ) -> str:
        """Process the response from the API call.

        This method must be implemented in the child class for specific API
        implementations.

        Args:
            content_tuple: Tuple of content, tokens, and finish reason.
            api_payload: Dictionary containing API parameters.
            retry_count: Current retry attempt count.
            json_response: Whether response is in JSON format.
            assistant_message: Optional previous assistant message.

        Returns:
            The final processed response string.

        Raises:
            NotImplementedError: Must be implemented in child class.
        """
        raise NotImplementedError("Must be implemented in child class")

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Create a payload dictionary for making API calls to AI engine.

        Args:
            prompt: The prompt text for the AI model.
            role_script: The role script text for the AI model.
            temperature: The temperature value for the AI model.
            max_tokens: The maximum number of tokens for the AI model.

        Returns:
            The payload dictionary containing model parameters.

        Raises:
            AttributeError: If AI model not set.
            ValidationError: If payload validation fails.
        """
        if not self.api_model:
            raise AttributeError("AI model not set. Call set_model() first.")
        try:
            payload = Payload(
                api_model=self.api_model,
                role_script=role_script,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return payload.model_dump()
        except ValidationError as e:
            logger.exception(str(e))
            raise

    def modify_payload(self, api_payload: dict, **kwargs) -> dict:
        """Modify the given api_payload dictionary with provided kwargs.

        Args:
            api_payload: The original api_payload dictionary.
            **kwargs: The key-value pairs to update the dictionary.

        Returns:
            The modified api_payload dictionary.
        """
        api_payload |= kwargs
        return api_payload

    def set_model(self, model: Model, rate_handler: RateLimitManager) -> None:
        """Set the specific AI model to be used and initialize rate limiter.

        Args:
            model: The model object to use for the AI engine.
            rate_handler: The rate limit manager to use.
        """
        self.model = model

        self.api_model = self.model.api_model
        self.rate_limiter = RateLimit(
            self.model.name, self.model.rate_limit, rate_handler
        )

    def _enforce_rate_limit(self, input_tokens: int, max_tokens: int) -> None:
        """Handle rate limiting for API calls to the AI engine.

        Uses the RateLimit class to self-police the API rate limit by
        executing a cool down period when approaching the rate limit.

        Args:
            input_tokens: The number of tokens used in the API call.
            max_tokens: The maximum number of tokens allowed for the call.
        """
        if self.rate_limiter.is_rate_limit_exceeded(input_tokens, max_tokens):
            self.rate_limiter.cool_down()

    def _error_handle(self, e: Exception, retry_count: int = 0) -> int:
        """Call the error handler to determine if exception is recoverable.

        Determines if the exception is recoverable or not. If it is, an
        updated retry count is returned. If not, the error is logged and
        the application exits.

        Args:
            e: Exception to handle.
            retry_count: The number of attempts so far.

        Returns:
            The updated retry count.
        """
        return self.error_handler.handle_error(e, retry_count)

    def _update_rate_limit_dict(self, tokens: int) -> None:
        """Update the rate limit data by adding the number of tokens used.

        Args:
            tokens: The number of tokens used in the API call.
        """
        self.rate_limiter.rate_limit_dict["tokens_used"] += tokens
        self.rate_limiter.update_rate_limit_dict()
