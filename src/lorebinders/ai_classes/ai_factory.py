import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from _types import ChatCompletion, ErrorManager, FinishReason
from exceptions import MaxRetryError
from file_handling import read_json_file, write_json_file
from pydantic import BaseModel, ValidationError


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

    def __init__(
        self,
        error_manager: ErrorManager,
        model_key: str,
    ) -> None:
        self._error_handler = error_manager
        self.model_key = model_key

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
        retry_count: int = 0,
        assistant_message: Optional[str] = None,
    ) -> str:
        """
        Dummy method. Do not use.
        """
        return "Do not use this method"


class RateLimit:
    def __init__(self, model_key: str) -> None:
        self._model_key = model_key
        self.model_details()
        self._set_rate_limit_data()

    def _set_rate_limit_data(self) -> None:
        self._rate_limit_data: dict = (
            read_json_file("rate_limit.json")
            if os.path.exists("rate_limit.json")
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

    def model_details(self) -> None:
        model_details = self.get_model_details(self._model_key)
        self.model_name: str = model_details["model_name"]
        self._rate_limit: int = model_details["rate_limt"]
        self.context_window: int = model_details["context_window"]
        self.tokenizer: str = model_details["tozenizer"]

    def get_model_details(self, model_key: str) -> dict:
        """
        Interprets the generic model key and returns model-specific details.

        Args:
            model_key (str): The key used to identify the model.

        Returns:
            dict: A dictionary containing the model-specific details. The
            dictionary has the following keys:
                    model_name (str): The name of the model.
                    rate_limit (int): The rate limit for the model.
                    context_window (int): The size of the context window for
                        the model.
                    tokenizer (str): The tokenizer used by the model.

        Raises:
            FileNotFoundError: If the model_dict.json file is not found.
            json.JSONDecodeError: If there is an error decoding the
                model_dict.json file.

        """
        defaults: dict = {
            "model_name": None,
            "rate_limit": 250000,
            "context_window": 4096,
            "tokenizer": "tiktoken",
        }
        try:
            model_dict = (
                read_json_file("model_dict.json")
                if os.path.exists("model_dict.json")
                else {}
            )
            if isinstance(model_dict, dict):
                model_details: dict = model_dict.get(model_key, defaults)
        except (FileNotFoundError, json.JSONDecodeError):
            model_details = defaults
        return model_details

    def is_rate_limit(self, model_key: str) -> int:
        """
        Returns the rate limit based on the model key.

        Args:
            model_key (str): The key used to identify the model.

        Returns:
            int: The rate limit for the model.

        Raises:
            ValueError: If the model_key input is not a non-empty string.
            ValueError: If the rate limit is not an integer.
        """
        if not isinstance(model_key, str) or not model_key:
            raise ValueError(
                "Invalid model_key input. Expected a non-empty string."
            )

        if model_key not in self._rate_limit_data:
            self._rate_limit_data[model_key] = self.get_model_details(
                model_key
            )

        model_details = self._rate_limit_data[model_key]

        if model_details is None:
            return 0

        rate_limit = model_details.get("rate_limit")

        if not isinstance(rate_limit, int):
            raise ValueError("Rate limit must be an integer.")

        return rate_limit


class AIFactory(AIType, ABC, RateLimit):
    def __init__(
        self,
        error_manager: ErrorManager,
        model_key: str,
    ) -> None:
        self._error_handler = error_manager

        RateLimit.__init__(self, model_key)
        self.unresolvable_error_handler = self._set_unresolvable_errors()

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
        api_payload.update(kwargs)
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
            retry_count: the number of attemps so far
        """
        try:
            response = getattr(e, "response", None)
            if response:
                error_details = response.json().get("error", {})
        except (AttributeError, json.JSONDecodeError):
            error_details = {}

        error_code = getattr(e, "status_code", None)
        error_message = error_details.get("message", "Unknown error")

        if isinstance(e, tuple(self.unresolvable_error_handler)):
            self._error_handler.kill_app(e)
        if error_code == 401:
            self._error_handler.kill_app(e)
        if "exceeded your current quota" in error_message:
            self._error_handler.kill_app(e)

        logging.error(f"An error occurred: {e}", exc_info=True)

        MAX_RETRY_COUNT = 5

        try:
            retry_count += 1
            if retry_count == MAX_RETRY_COUNT:
                raise MaxRetryError("Maximum retry count reached")
            else:
                sleep_time = (MAX_RETRY_COUNT - retry_count) + (retry_count**2)
                logging.warning(
                    f"Retry attempt #{retry_count} in {sleep_time} seconds."
                )
        except MaxRetryError as e:
            self._error_handler.kill_app(e)

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
        retry_count: Optional[int] = 0,
        assistant_message: Optional[str] = None,
    ) -> str:
        """
        Makes API calls to the AI engine.
        This method smust be implemented in the child class for specific API
        implementations.
        """
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def process_response(
        self, response: ChatCompletion
    ) -> Tuple[str, int, FinishReason]:
        raise NotImplementedError("Must be implemented in child class")

    @abstractmethod
    def _set_unresolvable_errors(self) -> tuple:
        raise NotImplementedError("Must be implemented in child class")
