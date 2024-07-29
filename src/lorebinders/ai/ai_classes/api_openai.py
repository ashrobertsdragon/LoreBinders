from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast

import openai
import tiktoken
from loguru import logger
from openai import OpenAI

if TYPE_CHECKING:
    from lorebinders._type_annotations import (
        EmailManager,
        ChatCompletion,
        ChatCompletionAssistantMessageParam,
        ChatCompletionSystemMessageParam,
        ChatCompletionUserMessageParam,
        FinishReason,
        ResponseFormat,
    )

from lorebinders.ai.ai_factory import AIManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError
from lorebinders.json_tools import MergeJSON, RepairJSON


class OpenaiAPI(AIManager):
    """
    Child class of AIManager that implements the OpenAI API.
    """

    def __init__(self, email_handler: EmailManager) -> None:
        """
        Initialize the OpenAI client and unresolvable errors.
        """
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )

        self._initialize_client()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _initialize_client(self) -> None:
        """Create the OpenAI API client with the API key"""
        try:
            if api_key := os.environ.get("OPENAI_API_KEY"):
                self.client = OpenAI(api_key=api_key)
            else:
                raise KeyNotFoundError(
                    "OPENAI_API_KEY environment variable not set"
                )
        except KeyNotFoundError as e:
            self._error_handle(e)

    def _set_unresolvable_errors(self) -> tuple:
        """Set the unresolvable errors for OpenAI's API"""
        return (
            KeyNotFoundError,
            openai.BadRequestError,
            openai.AuthenticationError,
            openai.NotFoundError,
            openai.PermissionDeniedError,
            openai.UnprocessableEntityError,
        )

    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]:
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

        Note: Parameter dictionaries are typed to OpenAI's custom TypedDicts
        to keep MyPy happy.
        """
        role_dict: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": role_script,
        }
        prompt_dict: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt,
        }
        messages: list = [role_dict, prompt_dict]

        if assistant_message is not None:
            messages = self._add_assistant_message(messages, assistant_message)

        combined_text = "".join([
            cast(str, msg["content"]) for msg in messages
        ])
        input_tokens = self._count_tokens(combined_text)
        return messages, input_tokens

    def _add_assistant_message(
        self,
        messages: list,
        assistant_message: str,
    ) -> list:
        """
        Append the assistant message and continuation prompt to the message
        list.
        """
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

        return messages

    def _count_tokens(self, text: str) -> int:
        """
        Counts tokens using the tokenizer for the AI model.
        """
        return len(self.tokenizer.encode(text))

    def call_api(
        self,
        api_payload: dict[str, str],
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
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
            role_script=role_script,
            prompt=prompt,
            assistant_message=assistant_message,
        )

        try:
            return self._make_api_call(
                api_payload=api_payload,
                messages=messages,
                input_tokens=input_tokens,
                json_response=json_response,
                retry_count=retry_count,
                assistant_message=assistant_message,
            )
        except Exception as e:
            retry_count = self._error_handle(e, retry_count)
            return self.call_api(
                api_payload=api_payload,
                json_response=json_response,
                retry_count=retry_count,
                assistant_message=assistant_message,
            )

    def _make_api_call(
        self,
        api_payload: dict[str, str],
        messages: list,
        input_tokens: int,
        json_response: bool,
        retry_count: int,
        assistant_message: str | None = None,
    ) -> str:
        """Performs the actual OpenAI API call."""
        self._enforce_rate_limit(input_tokens, int(api_payload["max_tokens"]))
        model = api_payload["api_model"]
        max_tokens = int(api_payload["max_tokens"])
        temperature = float(api_payload["temperature"])

        response_format: ResponseFormat = (
            {"type": "json_object"} if json_response else {"type": "text"}
        )

        response: ChatCompletion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content_tuple = self.preprocess_response(response)
        return self.process_response(
            content_tuple=content_tuple,
            api_payload=api_payload,
            retry_count=retry_count,
            json_response=json_response,
            assistant_message=assistant_message,
        )

    def preprocess_response(
        self, response: ChatCompletion
    ) -> tuple[str, int, FinishReason]:
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
            self.rate_limiter.update_tokens_used(tokens)
        else:
            logger.exception("No message content found")
            raise NoMessageError("No message content found")

        return content, completion_tokens, finish_reason

    def process_response(
        self,
        content_tuple: tuple[str, int, FinishReason],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        assistant_message: str | None = None,
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
            answer = self._combine_answer(
                assistant_message=assistant_message,
                content=content,
                json_response=json_response,
            )
        else:
            answer = content

        if finish_reason == "length":
            return self._handle_length_limit(
                answer=answer,
                api_payload=api_payload,
                retry_count=retry_count,
                json_response=json_response,
                completion_tokens=completion_tokens,
            )

        return answer

    def _combine_answer(
        self, assistant_message: str, content: str, json_response: bool
    ) -> str:
        """
        Combine assistant message and new content based on response format.
        """
        if json_response:
            merge = MergeJSON()
            repair = RepairJSON()
            new_part = content[1:]
            merge.set_ends(assistant_message, new_part)
            return merge.merge() or repair.repair_str(
                assistant_message + new_part
            )
        return assistant_message + content

    def _handle_length_limit(
        self,
        answer: str,
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        completion_tokens: int,
    ) -> str:
        """Handle cases where the response exceeds the maximum token limit."""
        MAX_TOKENS = 500
        logger.warning(
            f"Max tokens exceeded.\n"
            f"Used {completion_tokens} of {api_payload.get("max_tokens")}"
        )

        if json_response:
            last_complete = answer.rfind("},")
            assistant_message = (
                answer[: last_complete + 1] if last_complete > 0 else ""
            )
        else:
            assistant_message = answer

        api_payload = self.modify_payload(api_payload, max_tokens=MAX_TOKENS)
        return self.call_api(
            api_payload=api_payload,
            json_response=json_response,
            retry_count=retry_count,
            assistant_message=assistant_message,
        )
