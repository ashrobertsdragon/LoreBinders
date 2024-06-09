import logging
import os
from typing import Dict, Optional, Tuple

from _types import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ErrorManager,
    FileManager,
    FinishReason,
    NoMessageError,
    ResponseFormat,
)
from ai_factory import AIFactory
from exceptions import KeyNotFoundError
from json_repairer import JSONRepair
from openai import OpenAI


class OpenaiAPI(AIFactory):
    """
    Child class of AIInterface.
    """

    def __init__(
        self,
        file_manager: FileManager,
        error_manager: ErrorManager,
        model_key: str,
    ) -> None:
        """
        Initialize the model details and the OpenAI client.
        """
        super().__init__(file_manager, error_manager, model_key)
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise KeyNotFoundError(
                    "OPENAI_API_KEY environment variable not set"
                )
            self.openai_client = OpenAI(api_key=api_key)
        except KeyNotFoundError as e:
            self.errors.kill_app(e)

    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: Optional[str] = None,
    ) -> Tuple[list, int]:
        """
        Creates a payload for making API calls to the AI engine.

        Args:
            role_script (str): The role script text for the AI model.
            prompt (str): The prompt text for the AI model.
            assistant_message (Optional[str], optional): The assistant message
                text. Defaults to None.

        Returns:
            Tuple[list, int]: A tuple containing a list of messages and the
                number of input tokens.

        Raises:
            ValueError: If the role_script input is not a string.
            ValueError: If the prompt input is not a string.

        """
        role_dict: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": role_script,
        }
        prompt_dict: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt,
        }
        messages = [role_dict, prompt_dict]
        added_prompt = ""
        if assistant_message is not None:
            added_prompt = (
                "Please continue from the exact point you left off without "
                "any commentary"
            )
            assistant_dict: ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": assistant_message,
            }
            added_prompt_dict: ChatCompletionUserMessageParam = {
                "role": "user",
                "content": added_prompt,
            }
            messages.extend([assistant_dict, added_prompt_dict])
        combined_text = "".join([prompt, role_script])
        input_tokens = self.count_tokens(
            f"{combined_text}{assistant_message}{added_prompt}"
        )
        return messages, input_tokens

    def call_api(
        self,
        api_payload: Dict[str, str],
        retry_count: int = 0,
        json_response: bool = False,
        assistant_message: Optional[str] = None,
    ) -> str:
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
        prompt = api_payload["prompt"]
        role_script = api_payload["role_script"]
        messages, input_tokens = self.create_message_payload(
            role_script, prompt, assistant_message
        )
        model_name = api_payload["model_name"]
        max_tokens = int(api_payload["max_tokens"])
        temperature = float(api_payload["temperature"])

        self.handle_rate_limiting(input_tokens, max_tokens)
        response_format: ResponseFormat = (
            {"type": "json_object"} if json_response else {"type": "text"}
        )

        try:
            response: ChatCompletion = (
                self.openai_client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    temperature=temperature,
                )
            )
            content_tuple = self.preprocess_response(response)
            answer = self.process_response(
                content_tuple,
                assistant_message,
                api_payload,
                retry_count,
                json_response,
            )
        except Exception as e:
            retry_count = self.error_handle(e, retry_count)
            answer = self.call_api(
                api_payload, retry_count, json_response, assistant_message
            )

        return answer

    def preprocess_response(
        self, response: ChatCompletion
    ) -> Tuple[str, int, FinishReason]:
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
        if (
            response.choices
            and response.choices[0].message.content
            and response.usage
        ):
            content: str = response.choices[0].message.content.strip()
            tokens: int = response.usage.total_tokens
            completion_tokens: int = response.usage.completion_tokens
            finish_reason: FinishReason = response.choices[0].finish_reason
            self.update_rate_limit_data(tokens)
        else:
            logging.exception("No message content found")
            raise NoMessageError("No message content found")

        return content, completion_tokens, finish_reason

    def process_response(
        self,
        content_tuple: Tuple[str, int, FinishReason],
        assistant_message: Optional[str],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
    ) -> str:
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
        content, completion_tokens, finish_reason = content_tuple
        if assistant_message:
            if json_response:
                repair = JSONRepair()
                new_part = content[1:]
                combined = repair.merge(assistant_message, new_part)
                if combined:
                    answer = combined
                else:
                    answer = repair.repair_str(assistant_message + new_part)
            else:
                answer = assistant_message + content
        else:
            answer = content

        if finish_reason == "length":
            length_warning = (
                "Max tokens exceeded.\n"
                f"Used {completion_tokens} of {api_payload.get("max_tokens")}"
            )
            logging.warning(length_warning)
            if json_response:
                last_complete = answer.rfind("},")
                assistant_message = (
                    answer[: last_complete + 1] if last_complete > 0 else ""
                )
            else:
                assistant_message = answer
            MAX_TOKENS = 500
            api_payload = self.modify_payload(
                api_payload, max_tokens=MAX_TOKENS
            )
            answer = self.call_api(
                api_payload, retry_count, json_response, assistant_message
            )

        return answer
