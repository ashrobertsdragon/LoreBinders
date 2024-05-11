import logging
import os
from typing import Optional, Tuple

from openai import OpenAI

from ai_classes import FinishReason, ChatCompletion
from ai_interface import AIInterface
from exceptions import NoMessageError
from error_handler import ErrorHandler
from file_handling import FileHandler
from json_repair import JSONRepair

errors = ErrorHandler()
files = FileHandler()
repair = JSONRepair()

class OpenAIAPI(AIInterface):
    """
    Child class of AIInterface.
    """
    def __init__(self):
        """
        Initialize the model details and the OpenAI client.
        """
        super().__init__()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            errors.kill_app("OPENAI_API_KEY environment variable not set")
        self.openai_client = OpenAI()

    def call_api(self, api_payload: dict, retry_count: Optional[int] = 0, assistant_message: Optional[str] = None, json_response: Optional[bool] = False) -> str:
        """
        Process the response received from the OpenAI API.

        Args:
            response (ChatCompletion): The response object received from the
                OpenAI API.

        Returns:
            Tuple[str, int, FinishReason]: A tuple containing the content of
                the response, the number of completion tokens used, and the
                reason for the completion of the response.

        Raises:
            NoMessageError: If no message content is found in the response.
        """
        super().call_api()
        response_format = {"type": "json_object"} if json_response else {"type": "text"}

        try:
            response: ChatCompletion = self.openai_client.chat.completions.create(
                model=api_payload.get("model_name"),
                messages=api_payload.get("messages"),
                temperature=api_payload.get("temperature"),
                max_tokens=api_payload.get("max_tokens"),
                response_format=response_format
            )
            content = self.process_response(response, json_response)
        except Exception as e:
            retry_count: int = self.error_handle(e, retry_count)
            content = self.call_api(api_payload, retry_count, assistant_message, json_response)

        answer = self.postprocess_response(content, assistant_message, api_payload, retry_count, json_response)
        return answer

    def process_response(self, response: ChatCompletion) -> Tuple[str, int, FinishReason]:
        """
        Process the response received from the OpenAI API.

        Args:
            response (ChatCompletion): The response object received from the
                OpenAI API.

        Returns:
            Tuple[str, int, FinishReason]: A tuple containing the content of
                the response, the number of completion tokens used, and the
                reason for the completion of the response.

        Raises:
            NoMessageError: If no message content is found in the response.
        """
        if response.choices and response.choices[0].message:
            content: str = response.choices[0].message.get('content').strip()
            tokens: int = response.usage.total_tokens
            completion_tokens: int = response.usage.completion_tokens
            finish_reason: FinishReason = response.choices[0].finish_reason
            self.update_rate_limit_data(tokens)
        else:
            logging.exception("No message content found")
            raise NoMessageError("No message content found")

        return content, completion_tokens, finish_reason



    def postprocess_response(self, content: str, completion_tokens: int, finish_reason: FinishReason, assistant_message: str, api_payload: dict, retry_count: int, json_response: bool) -> str:
        """
        Post-processes the response received from the OpenAI API.

        Args:
            content (str): The content of the response.
            completion_tokens (int): The number of completion tokens used in
                the response.
            finish_reason (FinishReason): The reason for the completion of the
                response.
            assistant_message (str): The assistant message used in the API
            call.
            api_payload (dict): The payload used in the API call.
            retry_count (int): The number of retries made for the API call.
            json_response (bool): Flag indicating whether the response is in
                JSON format.

        Returns:
            str: The processed response.

        Raises:
            NoMessageError: If no message content is found in the response.

        Notes:
            If an assistant message is provided, the response is combined with
                the assistant message.
            If the response is in JSON format, the response is merged with the
                assistant message using the 'merge' method of the 'repair'
                object.
            If the response cannot be merged with the assistant message, the
                response is repaired using the 'repair' method of the 'repair'
                object.
            If no assistant message is provided, the response is returned as
                is.
            If the finish reason is 'FinishReason.LENGTH', a warning is logged
                and the response is modified to fit within the maximum token
                limit.
            If the response is in JSON format, the assistant message is
                extracted from the response.
            The maximum token limit is set to 500.
            The API call is made again with the modified payload.
        """
        if assistant_message:
            if json_response:
                new_part = content[1:]
                combined = repair.merge(assistant_message, new_part)
                if combined:
                    answer = combined
                else:
                    answer = repair.repair(assistant_message + new_part)
            else:
                answer = assistant_message + content
        else:
            answer = content

        if finish_reason == FinishReason.LENGTH:
            length_warning = f"Max tokens exceeded.\nUsed {completion_tokens} of {api_payload.get("max_tokens")}"
            logging.warning(length_warning)
            if json_response:
                last_complete = answer.rfind("},")
                assistant_message = answer[:last_complete + 1] if last_complete > 0 else ""
            else:
                assistant_message = answer
            MAX_TOKENS = 500
            api_payload = self.modify_payload(api_payload, max_tokens=MAX_TOKENS)
            answer = self.call_api(api_payload, retry_count, assistant_message, json_response)

        return answer