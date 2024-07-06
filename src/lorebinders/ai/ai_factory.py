from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from .api_error_handler import APIErrorHandler
from .rate_limit import RateLimit

if TYPE_CHECKING:
    from .ai_models._model_schema import Model

    from lorebinders._managers import EmailManager, RateLimitManager
    from lorebinders._types import ChatCompletion, FinishReason


class Payload(BaseModel):
    api_model: str
    role_script: str
    prompt: str
    temperature: float
    max_tokens: int


class AIManager(ABC):
    def __init__(self, email_handler: EmailManager) -> None:
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )

    @abstractmethod
    def _set_unresolvable_errors(self) -> tuple:
        """
        Set a tuple of errors that are unrecoverable in the API.
        This method must be implemented in the child class for specific API.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _count_tokens(self, text: str) -> int:
        """
        Counts tokens using the tokenizer for the AI model.
        This method must be implemented in the child class for specific API
        implementations.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]:
        """
        Creates the message payload for the API call.
        This method must be implemented in the child class for specific API
        implementations.
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
        """
        Makes API calls to the AI engine.
        This method must be implemented in the child class for specific API
        implementations.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]:
        """
        Create a tuple from the response from the API call.
        This method must be implemented in the child class for specific API
        implementations.
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
        """
        Processes the response from the API call.
        This method must be implemented in the child class for specific API
        implementations.
        """
        raise NotImplementedError("Must be implemented in child class")

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """
        Creates a payload dictionary for making API calls to the AI engine.

        Args:
            prompt (str): The prompt text for the AI model.
            role_script (str): The role script text for the AI model.
            temperature (float): The temperature value for the AI model.
            max_tokens (int): The maximum number of tokens for the AI model.

        Returns:
            dict: The payload dictionary containing the following keys:
                    model_name (str): The name of the model.
                    role_script (str): The role script text.
                    prompt (str): The prompt text.
                    temperature (float): The temperature value.
                    max_tokens (int): The maximum number of tokens.
        """

        try:
            payload = Payload(
                api_model=self.api_model,
                role_script=role_script,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ValidationError as e:
            logging.exception(str(e))

        return payload.model_dump()

    def modify_payload(self, api_payload: dict, **kwargs) -> dict:
        """
        Modifies the given api_payload dictionary with the provided key-value
            pairs in kwargs.

        Args:
            api_payload (dict): The original api_payload dictionary.
            **kwargs: The key-value pairs to update the api_payload dictionary.

        Returns:
            dict: The modified api_payload dictionary.
        """
        api_payload |= kwargs
        return api_payload

    def set_model(self, model: Model, rate_handler: RateLimitManager) -> None:
        """
        Sets the specific AI model to be used in the API and initializes the
        rate limiter for the model.

        Args:
            model (Model): The model object to use for the AI engine.
            rate_handler (RateLimitManager): The rate limit manager to use.
        """
        self.model = model

        self.api_model = self.model.api_model
        self.rate_limiter = RateLimit(
            self.model.name, self.model.rate_limit, rate_handler
        )

    def _enforce_rate_limit(self, input_tokens: int, max_tokens: int) -> None:
        """
        Handles rate limiting for API calls to the AI engine.

        This method uses the RateLimit class to self-police the API rate limit
        by executing a cool down period when approaching the rate limit.

        Args:
            input_tokens (int): The number of tokens used in the API call.
            max_tokens (int): The maximum number of tokens allowed for the API
                call.
        """
        if self.rate_limiter.is_rate_limit_exceeded(input_tokens, max_tokens):
            self.rate_limiter.cool_down()

    def _error_handle(self, e: Exception, retry_count: int = 0) -> int:
        """
        Calls the 'handle_error' method of the error handler class which
        determines if the exception is recoverable or not. If it is, an
        updated retry count is returned. If not, the error is logged, and the
        application exits.

        Args:
            e: an Exception body
            retry_count: the number of attempts so far

        Returns:
            retry_count: the number of attempts so far
        """
        return self.error_handler.handle_error(e, retry_count)

    def _update_rate_limit_dict(self, tokens: int) -> None:
        """
        Updates the rate limit data by adding the number of tokens used.

        Args:
            tokens (int): The number of tokens used in the API call.
        """
        self.rate_limiter.rate_limit_dict["tokens_used"] += tokens
        self.rate_limiter.update_rate_limit_dict()
