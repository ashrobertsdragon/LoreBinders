import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from exceptions import MaxRetryError
from pydantic import BaseModel, ValidationError

from email_handler.send_email import SMTPHandler
from lorebinders._types import ChatCompletion, FinishReason
from lorebinders.error_handler import ErrorHandler
from lorebinders.file_handling import read_json_file, write_json_file

email_handler = SMTPHandler()
error_handling = ErrorHandler(email_manager=email_handler)


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
    def __init__(self, model_dict: dict) -> None:
        self.model_details(model_dict)
        self._set_rate_limit_data()

    def model_details(self, model_dict) -> None:
        self.model_name: str = model_dict["model"]
        self._rate_limit: int = model_dict["rate_limit"]
        self.context_window: int = model_dict["context_window"]
        self.tokenizer: str = model_dict["tokenizer"]

    def _set_rate_limit_data(self) -> None:
        self._rate_limit_data: dict = (
            read_json_file(f"{self.model_name}_rate_limit.json")
            if os.path.exists(f"{self.model_name}_rate_limit.json")
            else {}
        )
        self._reset_rate_limit_minute()
        self._reset_rate_limit_tokens_used()

    def _reset_rate_limit_minute(self) -> None:
        self._rate_limit_data["minute"] = self._rate_limit_data.get(
            "minute", time.time()
        )

    def _reset_rate_limit_tokens_used(self) -> None:
        self._rate_limit_data["tokens_used"] = self._rate_limit_data.get(
            "tokens_used", 0
        )

    def get_rate_limit_minute(self) -> float:
        return self._rate_limit_data["minute"]

    def get_rate_limit_tokens_used(self) -> int:
        return self._rate_limit_data["tokens_used"]

    def is_rate_limit(self) -> int:
        """
        Returns the rate limit.

        Returns:
            int: The rate limit for the model.
        """

        model_details = self._rate_limit_data

        if model_details is None:
            return 0

        rate_limit = model_details.get("rate_limit")

        if not isinstance(rate_limit, int):
            raise ValueError("Rate limit must be an integer.")

        return rate_limit


class AIFactory(AIType, ABC, RateLimit):
    def __init__(self) -> None:
        self.unresolvable_error_handler = self._set_unresolvable_errors()

    def set_model(self, model_dict: dict) -> None:
        self.model_dict = model_dict

        RateLimit.__init__(self, self.model_dict)
        self.model_name = self.model_dict["model"]

    def count_tokens(self, text: str) -> int:
        """
        Counts tokens using the tokenizer for the AI model.
        """
        return len(self.tokenizer.encode(text))

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

    def update_rate_limit_data(self, tokens: int) -> None:
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
                'rate_limit_data.json'.
        """
        self._rate_limit_data["tokens_used"] += tokens
        write_json_file(self._rate_limit_data, "rate_limit_data.json")

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

    def error_handle(self, e: Exception, retry_count: int) -> int:
        """
        Determines whether error is unresolvable or should be retried. If
        unresolvable, error is logged and administrator is emailed before
        exit. Otherwise, exponential backoff is used for up to 5 retries.

        Args:
            e: an Exception body
            retry_count: the number of attempts so far

        Returns:
            retry_count: the number of attempts so far
        """
        try:
            if response := getattr(e, "response", None):
                error_details = response.json().get("error", {})
        except (AttributeError, json.JSONDecodeError):
            error_details = {}

        error_code = getattr(e, "status_code", None)
        error_message = error_details.get("message", "Unknown error")

        if (
            isinstance(e, tuple(self.unresolvable_error_handler))
            or error_code == 401
            or "exceeded your current quota" in error_message
        ):
            error_handling.kill_app(e)

        logging.error(f"An error occurred: {e}", exc_info=True)

        MAX_RETRY_COUNT = 5

        try:
            retry_count += 1
            if retry_count == MAX_RETRY_COUNT:
                raise MaxRetryError("Maximum retry count reached")
            sleep_time = (MAX_RETRY_COUNT - retry_count) + (retry_count**2)
            logging.warning(
                f"Retry attempt #{retry_count} in {sleep_time} seconds."
            )
        except MaxRetryError as e:
            error_handling.kill_app(e)

        return retry_count

    def handle_rate_limiting(self, input_tokens: int, max_tokens: int) -> None:
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

        Returns:
            None

        Raises:
            None
        """
        minute = self.get_rate_limit_minute()
        tokens_used = self.get_rate_limit_tokens_used()

        if time.time() > minute + 60:
            self._reset_rate_limit_minute()
            self._reset_rate_limit_tokens_used()
            write_json_file(self._rate_limit_data, "rate_limit_data.json")

        if tokens_used + input_tokens + max_tokens > self._rate_limit:
            self._cool_down(minute)

    def _cool_down(self, minute):
        logging.warning("Rate limit exceeded")
        sleep_time = 60 - (time.time() - minute)
        logging.info(f"Sleeping {sleep_time} seconds")
        time.sleep(sleep_time)
        self._reset_rate_limit_tokens_used()
        self._reset_rate_limit_minute()
        write_json_file(self._rate_limit_data, "rate_limit_data.json")

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
