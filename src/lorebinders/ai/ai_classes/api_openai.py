from __future__ import annotations

from typing import TYPE_CHECKING, cast

import openai
import tiktoken
from decouple import config
from loguru import logger
from openai import OpenAI

if TYPE_CHECKING:
    from lorebinders._type_annotations import (
        ChatCompletion,
        ChatCompletionAssistantMessageParam,
        ChatCompletionSystemMessageParam,
        ChatCompletionUserMessageParam,
        EmailManager,
        FinishReason,
        ResponseFormat,
    )

from lorebinders.ai.ai_factory import AIManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError
from lorebinders.json_tools import merge_json, repair_json_str


class OpenaiAPI(AIManager):
    """Child class of AIManager that implements the OpenAI API."""

    def __init__(self, email_handler: EmailManager) -> None:
        """Initialize the OpenAI client and unresolvable errors.

        Args:
            email_handler: Email manager for error notifications.
        """
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )

        self._initialize_client()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _initialize_client(self) -> None:
        """Create the OpenAI API client with the API key.

        Raises:
            KeyNotFoundError: If OPENAI_API_KEY environment variable not set.
        """
        try:
            if api_key := config("OPENAI_API_KEY"):
                self.client = OpenAI(api_key=api_key)
            else:
                raise KeyNotFoundError(
                    "OPENAI_API_KEY environment variable not set"
                )
        except KeyNotFoundError as e:
            self._error_handle(e)

    def _set_unresolvable_errors(self) -> tuple:
        """Set the unresolvable errors for OpenAI's API.

        Returns:
            Tuple of unresolvable error types.
        """
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
        """Create a payload for making API calls to the AI engine.

        Args:
            role_script: The role script text for the AI model.
            prompt: The prompt text for the AI model.
            assistant_message: Optional assistant message text.

        Returns:
            Tuple containing list of messages and input token count.
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

        combined_text = "".join([cast(str, msg["content"]) for msg in messages])
        input_tokens = self._count_tokens(combined_text)
        return messages, input_tokens

    def _add_assistant_message(
        self,
        messages: list,
        assistant_message: str,
    ) -> list:
        """Append assistant message and continuation prompt to message list.

        Args:
            messages: List of message dictionaries.
            assistant_message: Assistant message to append.

        Returns:
            Updated list of messages.
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
        """Count tokens using the tokenizer for the AI model.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        return len(self.tokenizer.encode(text))

    def call_api(
        self,
        api_payload: dict[str, str],
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """Make an API call to the OpenAI API.

        Args:
            api_payload: Dictionary containing API parameters.
            json_response: Whether to expect JSON response format.
            retry_count: Current retry attempt count.
            assistant_message: Optional previous assistant message.

        Returns:
            The API response text.
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
        """Perform the actual OpenAI API call.

        Args:
            api_payload: Dictionary containing API parameters.
            messages: List of message dictionaries.
            input_tokens: Number of input tokens.
            json_response: Whether to expect JSON response format.
            retry_count: Current retry attempt count.
            assistant_message: Optional previous assistant message.

        Returns:
            The processed API response.
        """
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
        """Process the response received from the OpenAI API.

        Args:
            response: The response object received from the OpenAI API.

        Returns:
            Tuple of (content, completion_tokens, finish_reason).

        Raises:
            NoMessageError: If no message content found in response.
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
        """Post-process the response received from the OpenAI API.

        Args:
            content_tuple: Tuple of content, tokens, and finish reason.
            api_payload: Dictionary containing API parameters.
            retry_count: Current retry attempt count.
            json_response: Whether response is in JSON format.
            assistant_message: Optional previous assistant message.

        Returns:
            The final processed response string.
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
        """Combine assistant message and new content based on format.

        Args:
            assistant_message: Previous assistant message.
            content: New content to combine.
            json_response: Whether response is in JSON format.

        Returns:
            Combined response string.
        """
        if json_response:
            new_part = content[1:]
            merged = merge_json(assistant_message, new_part)
            return merged or repair_json_str(assistant_message + new_part)
        return assistant_message + content

    def _handle_length_limit(
        self,
        answer: str,
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        completion_tokens: int,
    ) -> str:
        """Handle cases where response exceeds maximum token limit.

        Args:
            answer: Current response answer.
            api_payload: Dictionary containing API parameters.
            retry_count: Current retry attempt count.
            json_response: Whether response is in JSON format.
            completion_tokens: Number of completion tokens used.

        Returns:
            Complete response after handling length limit.
        """
        max_tokens = 500
        logger.warning(
            f"Max tokens exceeded.\n"
            f"Used {completion_tokens} of {api_payload.get('max_tokens')}"
        )

        if json_response:
            last_complete = answer.rfind("},")
            assistant_message = (
                answer[: last_complete + 1] if last_complete > 0 else ""
            )
        else:
            assistant_message = answer

        api_payload = self.modify_payload(api_payload, max_tokens=max_tokens)
        return self.call_api(
            api_payload=api_payload,
            json_response=json_response,
            retry_count=retry_count,
            assistant_message=assistant_message,
        )
