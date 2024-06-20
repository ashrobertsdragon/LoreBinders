import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from pydantic import BaseModel, ValidationError

from email_handlers.smtp_handler import SMTPHandler
from lorebinders._managers import RateLimitManager
from lorebinders._types import ChatCompletion, FinishReason, Model
from lorebinders.error_handler import APIErrorHandler

email_handler = SMTPHandler()


class Payload(BaseModel):
    model_name: str
    role_script: str
    prompt: str
    temperature: float
    max_tokens: int


class AIType:
    """
    Dummy class to pacify MyPy. Not intended to be used
    """

    def create_payload(
        self,
        prompt: str,
        role_script: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """
        Dummy method. Do not use.
        """
        payload = Payload(
            model_name="Do not use",
            role_script=role_script,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return payload.model_dump()

    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: Optional[str] = None,
    ) -> str:
        """
        Dummy method. Do not use.
        """
        return "Do not use this method"

    def set_model(self, model_dict: dict) -> None:
        """
        Dummy method. Do not use.
        """
        pass


class RateLimit:
    def __init__(self, model: str, rate_handler: RateLimitManager) -> None:
        self.model = model
        self._rate_handler = rate_handler
        self.rate_limit_dict = self.read_rate_limit_dict(self.model)

    def read_rate_limit_dict(self) -> None:
        self.rate_limit_dict: dict = self._rate_handler.read(self.model)

    def update_rate_limit_dict(self) -> None:
        self._rate_handler.write(self.model, self.rate_limit_dict)

    def reset_rate_limit_dict(self) -> None:
        self._reset_minute()
        self._reset_tokens_used()
        self.write_rate_limit_dict()

    def _reset_minute(self) -> None:
        self.rate_limit_dict["minute"] = time.time()

    def _reset_tokens_used(self) -> None:
        self.rate_limit_dict["tokens_used"] = 0

    @property
    def minute(self) -> float:
        self.read_rate_limit_dict()
        return self.rate_limit_dict["minute"]

    @property
    def tokens_used(self) -> int:
        self.read_rate_limit_dict()
        return self.rate_limit_dict["tokens_used"]


class AIFactory(AIType, ABC):
    def __init__(self) -> None:
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler, unresolvable=self.unresolvable_errors
        )

    def set_model(self, model: Model, rate_handler: RateLimitManager) -> None:
        self.model = model

        self.model_name = self.model.model
        self.rate_limiter = RateLimit(self.model_name, rate_handler)
        self.tokenizer_class = self.model.tokenizer

    @abstractmethod
    def _count_tokens(self, text: str) -> int:
        """
        Counts tokens using the tokenizer for the AI model.
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
                model_name=self.model_name,
                role_script=role_script,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ValidationError as e:
            logging.exception(str(e))

        return payload.model_dump()

    def update_rate_limit_dict(self, tokens: int) -> None:
        """
        Updates the rate limit data by adding the number of tokens used.

        Args:
            tokens (int): The number of tokens used in the API call.

        Returns:
            None

        Notes:
            The rate limit data dictionary is updated by adding the number of
            tokens used to the 'tokens_used' key.
            The updated rate limit data is then written to a JSON file named
                'rate_limit_dict.json'.
        """
        self.rate_limit_dict["tokens_used"] += tokens
        self.rate_limiter.update_rate_limit_dict(self.rate_limit_dict)

    @abstractmethod
    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: Optional[str] = None,
    ) -> Tuple[list, int]:
        raise NotImplementedError("Must be implemented in child class")

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

    def _error_handle(self, e: Exception, retry_count: int) -> int:
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

    def _enforce_rate_limit(self, input_tokens: int, max_tokens: int) -> None:
        """
        Handles rate limiting for API calls to the AI engine.

        This method checks the rate limit for the API calls and handles the
        rate limiting logic. It ensures that the number of tokens used in the
        API call, along with the maximum tokens allowed, does not exceed the
        rate limit set for the model. If the rate limit is exceeded, the
        method will log a warning and sleep for a certain period of time
        before retrying the API call.

        Args:
            input_tokens (int): The number of tokens used in the API call.
            max_tokens (int): The maximum number of tokens allowed for the API
                call.
        """
        minute = self.rate_limiter.minute
        tokens_used = self.rate_limiter.tokens_used

        if time.time() > minute + 60:
            self.rate_limiter.reset_rate_limit_dict()

        if (
            tokens_used + input_tokens + max_tokens
            > self.rate_limiter.rate_limit
        ):
            self._cool_down(minute)

    def _cool_down(self, minute: float):
        """
        Pause the application thread while the rate limit is in danger of
        being exceeded.

        Args:
            minute (float): The timestamp of the last rate limit reset
        """

        logging.warning("Rate limit in danger of being exceeded")
        sleep_time = 60 - (time.time() - minute)
        logging.info(f"Sleeping {sleep_time} seconds")
        time.sleep(sleep_time)
        self.rate_limiter.reset_rate_limit_dict()

    @abstractmethod
    def call_api(
        self,
        api_payload: dict,
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: Optional[str] = None,
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
    ) -> Tuple[str, int, FinishReason]:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def process_response(
        self,
        content_tuple: Tuple[str, int, FinishReason],
        assistant_message: Optional[str],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
    ) -> str:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _set_unresolvable_errors(self) -> tuple:
        raise NotImplementedError("Must be implemented in child class")
