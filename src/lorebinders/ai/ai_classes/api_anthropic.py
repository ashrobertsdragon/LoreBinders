import anthropic
from anthropic._exceptions import (
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from anthropic._tokenizers import sync_get_tokenizer
from anthropic.types import ContentBlockDelta, Message
from decouple import config
from loguru import logger

from lorebinders._managers import EmailManager
from lorebinders.ai.ai_factory import AIManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError
from lorebinders.json_tools import merge_json, repair_json_str


class AnthropicAPI(AIManager):
    """
    Child class of AIManager that implements the Anthropic API.
    """

    def __init__(self, email_handler: EmailManager) -> None:
        """
        Initialize the Anthropic client and unresolvable errors.
        """
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )
        self._initialize_client()

    def _set_unresolvable_errors(self) -> tuple:
        """Set the unresolvable errors for Anthropic's API"""
        return (
            KeyNotFoundError,
            AuthenticationError,
            BadRequestError,
            PermissionDeniedError,
            NotFoundError,
            UnprocessableEntityError,
        )

    def _initialize_client(self) -> None:
        """Create the Anthropic API client with the API key"""
        try:
            if api_key := config("ANTHROPIC_API_KEY"):
                self.client = anthropic.Anthropic(api_key=api_key)
            else:
                raise KeyNotFoundError(
                    "ANTHROPIC_API_KEY environment variable not set"
                )
        except KeyNotFoundError as e:
            self.error_handle(e)

    def _count_tokens(self, text: str) -> int:
        """
        Counts tokens using the tokenizer for the AI model.

        Args:
            text (str): The text to count tokens for.

        Returns:
            int: The number of tokens.
        """
        tokenizer = sync_get_tokenizer()
        return len(tokenizer(text))

    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list, int]:
        """
        Creates a payload for making API calls to the AI engine.
        """
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        if assistant_message is not None:
            messages.extend([
                {"role": "assistant", "content": assistant_message},
                {
                    "role": "user",
                    "content": "Please continue from the exact point you left"
                    + " off without any commentary",
                },
            ])

        combined_text = role_script + "".join([
            msg["content"] for msg in messages
        ])
        input_tokens = self._count_tokens(combined_text)
        return messages, input_tokens, role_script

    def call_api(
        self,
        api_payload: dict[str, str],
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """
        Make an API call to the Anthropic API.
        """
        prompt = api_payload["prompt"]
        role_script = api_payload["role_script"]
        messages, input_tokens, system = self.create_message_payload(
            role_script=role_script,
            prompt=prompt,
            assistant_message=assistant_message,
        )
        try:
            return self._make_api_call(
                api_payload=api_payload,
                messages=messages,
                system=system,
                input_tokens=input_tokens,
                json_response=json_response,
                retry_count=retry_count,
                assistant_message=assistant_message,
            )
        except RateLimitError:
            self.rate_limiter.cool_down()
        except Exception as e:
            retry_count = self.error_handle(e, retry_count)
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
        system: str,
        input_tokens: int,
        json_response: bool,
        retry_count: int,
        assistant_message: str | None = None,
    ) -> str:
        """Performs the actual Anthropic API call."""
        self._enforce_rate_limit(input_tokens, int(api_payload["max_tokens"]))
        model = api_payload["api_model"]
        max_tokens = int(api_payload["max_tokens"])
        temperature = float(api_payload["temperature"])

        response: Message = self.client.messages.create(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if isinstance(response, APIStatusError):
            raise response

        content_tuple = self.preprocess_response(response)
        return self.process_response(
            content_tuple=content_tuple,
            api_payload=api_payload,
            retry_count=retry_count,
            json_response=json_response,
            assistant_message=assistant_message,
        )

    def preprocess_response(self, response: Message) -> tuple[str, int, str]:
        """
        Process the response received from the Anthropic API.
        """
        if response.content and response.usage:
            content: str = "".join([
                block.text
                for block in response.content
                if isinstance(block, ContentBlockDelta)
            ])
            tokens: int = (
                response.usage.input_tokens + response.usage.output_tokens
            )
            completion_tokens: int = response.usage.output_tokens
            stop_reason: str = response.stop_reason
            self.rate_limiter.update_tokens_used(tokens)
        else:
            logger.exception("No message content found")
            raise NoMessageError("No message content found")
        return content, completion_tokens, stop_reason

    def process_response(
        self,
        content_tuple: tuple[str, int, str],
        api_payload: dict,
        retry_count: int,
        json_response: bool,
        assistant_message: str | None = None,
    ) -> str:
        """
        Post-processes the response received from the Anthropic API.
        """
        content, completion_tokens, stop_reason = content_tuple
        if assistant_message:
            answer = self._combine_answer(
                assistant_message=assistant_message,
                content=content,
                json_response=json_response,
            )
        else:
            answer = content
        if stop_reason == "max_tokens":
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
        """Handle cases where the response exceeds the maximum token limit."""
        MAX_TOKENS = 500
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
        api_payload = self.modify_payload(api_payload, max_tokens=MAX_TOKENS)
        return self.call_api(
            api_payload=api_payload,
            json_response=json_response,
            retry_count=retry_count,
            assistant_message=assistant_message,
        )
