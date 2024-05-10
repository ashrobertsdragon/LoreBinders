import backoff
from pydantic import BaseModel
import logging
import json
import os
import time
from typing import Optional, Tuple

from error_handler import ErrorHandler
from file_handling import FileHandler

errors = ErrorHandler()

class AIInterface():
    """
    Interface for interactions with API's for any AI's to be used now or in
    the future.
    """

    def __init__(self, model_key: str, files: FileHandler) -> None:
        self.rate_limit_data = files.read_json_file("rate_limit.json") if os.path.exists(
            "rate_limit.json") else {}
        self.rate_limit_data["tokens_used"] = self.rate_limit_data.get("tokens_used", 0)
        self.rate_limit_data["minute"] = self.rate_limit_data.get("minute", time.time())
        self.files = files
        for key, value in self.get_model_details(model_key):
            setattr(self, key, value)
        

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
            json.JSONDecodeError: If there is an error decoding the model_dict.json file.

        """
        defaults: dict = {"model_name": None, "rate_limit": 250000, "context_window": 4096, "tokenizer": "tiktoken"}
        try:
            model_dict: dict = self.files.read_json_file("model_dict.json") if os.path.exists("model_dict.json") else {}
            model_details: dict = model_dict.get(model_key, defaults)
        except (FileNotFoundError, json.JSONDecodeError):
            model_details: dict = defaults
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
            raise ValueError("Invalid model_key input. Expected a non-empty string.")
    
        if model_key not in self.rate_limit_data:
            self.rate_limit_data[model_key] = self.get_model_details(model_key)
    
        model_details = self.rate_limit_data[model_key]
    
        if model_details is None:
            return 0
    
        rate_limit = model_details.get("rate_limit")
    
        if not isinstance(rate_limit, int):
            raise ValueError("Rate limit must be an integer.")
    
        return rate_limit

    def count_tokens(self, text):
        """
        Counts tokens using the tokenizer for the AI model.
        """
        return len(self.tokenizer.encode(text))
    
    def create_payload(self, prompt: str,  role_script: str, temperature: float, max_tokens: int) -> dict:
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

        Raises:
            ValueError: If the prompt input is not a string.
            ValueError: If the role_script input is not a string.
            ValueError: If the temperature input is not a float.
            ValueError: If the max_tokens input is not an integer.
            ValueError: If the model name is not set.

        """
        class Payload(BaseModel):
            model_name: str
            role_script: str
            prompt: str
            temperature: float
            max_tokens: int

        if not isinstance(prompt, str):
            raise ValueError("Invalid prompt input. Expected a string.")
        if not isinstance(role_script, str):
            raise ValueError("Invalid role_script input. Expected a string.")
        if not isinstance(temperature, float):
            raise ValueError("Invalid temperature input. Expected a float.")
        if not isinstance(max_tokens, int):
            raise ValueError("Invalid max_tokens input. Expected an integer.")

        if self.model_name is None:
            raise ValueError("Model name is not set.")

        payload = Payload(
            model_name=self.model_name,
            role_script=role_script,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return payload.dict()
    
    def create_message_payload(self, role_script: str, prompt: str, assistant_message: Optional[str] = None) -> Tuple[list, int]:
        """
        Creates a payload for making API calls to the AI engine.

        Args:
            role_script (str): The role script text for the AI model.
            prompt (str): The prompt text for the AI model.
            assistant_message (Optional[str], optional): The assistant message text. Defaults to None.

        Returns:
            Tuple[list, int]: A tuple containing a list of messages and the number of input tokens.

        Raises:
            ValueError: If the role_script input is not a string.
            ValueError: If the prompt input is not a string.

        """
        combined_text = ''.join([prompt, role_script])
        messages = [
            {"role": "system", "content": role_script},
            {"role": "user", "content": prompt}
        ]
        added_prompt = ""
        if assistant_message is not None:
            added_prompt = "Please continue from the exact point you left off without any commentary"
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            messages.append({
                "role": "user",
                "content": added_prompt
            })
        input_tokens = self.count_tokens(combined_text, assistant_message, added_prompt)
        return messages, input_tokens
    
    def modify_payload(self, api_payload: dict, **kwargs) -> dict:
        """
        Modifies the given api_payload dictionary with the provided key-value pairs in kwargs.
    
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
        Determines whether error is unresolvable or should be retried. If unresolvable,
        error is logged and administrator is emailed before exit. Otherwise, exponential
        backoff is used for up to 5 retries.

        Args:
            e: an Exception body
            retry_count: the number of attempts so far

        Returns:
            retry_count: the number of attemps so far
        """
        try:
            error_details = getattr(e, "response", {}).json().get("error", {})
        except (AttributeError, json.JSONDecodeError):
            error_details = {}

        error_code = getattr(e, "status_code", None)
        error_message = error_details.get("message", "Unknown error")

        if isinstance(e, tuple(self.unresolvable_errors)):
            errors.kill_app(e)
        if error_code == 401:
            errors.kill_app(e)
        if "exceeded your current quota" in error_message:
            errors.kill_app(e)

        logging.error(f"An error occurred: {e}", exc_info=True)

        MAX_RETRY_COUNT = 5

        retry_count += 1
        if retry_count == MAX_RETRY_COUNT:
            errors.kill_app("Maximum retry count reached")
        else:
            sleep_time = (MAX_RETRY_COUNT - retry_count) + (retry_count ** 2)
            logging.warning(f"Retry attempt #{retry_count} in {sleep_time} seconds.")

            @backoff.on_exception(backoff.expo, Exception, max_tries=MAX_RETRY_COUNT)
            def retry_call():
                logging.warning(f"Retry attempt #{retry_count} in {sleep_time} seconds.")
                raise Exception()

            retry_call()

        return retry_count


    def handle_rate_limiting(self, input_tokens: int, max_tokens: int) -> None:
        minute = self.get_rate_limit_minute()
        tokens_used = self.get_rate_limit_tokens_used()

        if time.time() > minute + 60:
            self.set_rate_limit_minute(time.time())
            self.set_rate_limit_tokens_used(0)
            self.files.write_json_file(self.rate_limit_data, "rate_limit_data.json")

        if tokens_used + input_tokens + max_tokens > self.rate_limit:
            logging.warning("Rate limit exceeded")
            sleep_time = 60 - (time.time() - minute)
            logging.info(f"Sleeping {sleep_time} seconds")
            time.sleep(sleep_time)
            self.set_rate_limit_tokens_used(0)
            self.set_rate_limit_minute(time.time())
            self.files.write_json_file(self.rate_limit_data, "rate_limit_data.json")

    def call_api(self, api_payload: dict, retry_count: Optional[int] = 0, assistant_message: Optional[str] = None) -> str:
        """
        Makes API calls to the AI engine.
        This method should be extended in the child class for specific API
        implementations.
        """
        prompt = api_payload["prompt"]
        role_script = api_payload["role_script"]
        messages, input_tokens = self.create_message_payload(role_script, prompt, assistant_message)
        max_tokens = int(api_payload["max_tokens"])

        self.handle_rate_limiting(input_tokens, max_tokens)

        raise NotImplementedError("This method should be implemented in the child class.")