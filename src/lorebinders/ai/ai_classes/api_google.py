import google.generativeai as genai
from decouple import config
from google.generativeai.types import (
    Candidate,
    Content,
    FinishReason,
    GenerateContentRequest,
    GenerateContentResponse,
    GenerationConfig,
)
from loguru import logger

from lorebinders._managers import EmailManager
from lorebinders.ai.ai_factory import AIManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError
from lorebinders.json_tools import merge_json, repair_json_str


class GeminiAPI(AIManager):
    """Child class of AIManager that implements the Gemini API."""

    def __init__(self, email_handler: EmailManager) -> None:
        """Initialize the Gemini client and unresolvable errors.

        Args:
            email_handler: Email manager for error notifications.
        """
        self.unresolvable_errors = self._set_unresolvable_errors()
        self.error_handler = APIErrorHandler(
            email_manager=email_handler,
            unresolvable_errors=self.unresolvable_errors,
        )
        self._initialize_client()

    def _set_unresolvable_errors(self) -> tuple:
        """Set the unresolvable errors for Gemini's API.

        Returns:
            Tuple of unresolvable error types.
        """
        return (
            KeyNotFoundError,
            genai.errors.AuthenticationError,
            genai.errors.BadRequestError,
            genai.errors.PermissionDeniedError,
            genai.errors.NotFoundError,
            genai.errors.ResourceExhaustedError,  # Similar to RateLimitError
        )

    def _initialize_client(self) -> None:
        """Create the Gemini API client with the API key.

        Raises:
            KeyNotFoundError: If GEMINI_API_KEY environment variable not set.
        """
        try:
            if api_key := config("GEMINI_API_KEY"):
                genai.configure(api_key=api_key)
            else:
                raise KeyNotFoundError(
                    "GEMINI_API_KEY environment variable not set"
                )
        except KeyNotFoundError as e:
            self.error_handle(e)

    def _count_tokens(self, text: str) -> int:
        """Count tokens using the tokenizer for the AI model.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        # Note: Assuming self.api_model is set before calling this method
        model = genai.GenerativeModel(self.api_model)
        return model.count_tokens(text)

    def create_message_payload(
        self,
        role_script: str,
        prompt: str,
        assistant_message: str | None = None,
    ) -> tuple[list[Content], int]:
        """Create a payload for making API calls to the AI engine.

        Args:
            role_script: System instruction for the AI.
            prompt: User prompt for the AI.
            assistant_message: Optional previous assistant message.

        Returns:
            Tuple of (messages list, input token count).
        """
        messages: list[Content] = [Content(parts=[prompt], role="user")]
        if assistant_message is not None:
            messages.extend([
                Content(parts=[assistant_message], role="model"),
                Content(
                    parts=[
                        "Please continue from the exact point you left off "
                        "without any commentary"
                    ],
                    role="user",
                ),
            ])

        combined_text = role_script + "".join([
            "".join(content.parts) for content in messages
        ])
        input_tokens = self._count_tokens(combined_text)

        return messages, input_tokens

    def call_api(
        self,
        api_payload: dict[str, str],
        json_response: bool = False,
        retry_count: int = 0,
        assistant_message: str | None = None,
    ) -> str:
        """Make an API call to the Gemini API.

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
                role_script=role_script,
                api_payload=api_payload,
                messages=messages,
                input_tokens=input_tokens,
                json_response=json_response,
                retry_count=retry_count,
                assistant_message=assistant_message,
            )
        except genai.errors.ResourceExhaustedError:
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
        role_script: str,
        api_payload: dict[str, str],
        messages: list[Content],
        input_tokens: int,
        json_response: bool,
        retry_count: int,
        assistant_message: str | None = None,
    ) -> str:
        """Perform the actual Gemini API call.

        Args:
            role_script: System instruction for the AI.
            api_payload: Dictionary containing API parameters.
            messages: List of content messages.
            input_tokens: Number of input tokens.
            json_response: Whether to expect JSON response format.
            retry_count: Current retry attempt count.
            assistant_message: Optional previous assistant message.

        Returns:
            The processed API response.
        """
        self.enforce_rate_limit(input_tokens, int(api_payload["max_tokens"]))
        model = genai.GenerativeModel(api_payload["api_model"])
        max_tokens = int(api_payload["max_tokens"])
        temperature = float(api_payload["temperature"])

        response_mime_type: str = (
            "application/json" if json_response else "text/plain"
        )

        generation_config = GenerationConfig(
            system_instruction=role_script,
            response_mime_type=response_mime_type,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        request = GenerateContentRequest(
            contents=messages,
            generation_config=generation_config,
        )

        response: GenerateContentResponse = model.generate_content(
            request=request
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
        self, response: GenerateContentResponse
    ) -> tuple[str, int, FinishReason]:
        """Process the response received from the Gemini API.

        Args:
            response: The raw response from Gemini API.

        Returns:
            Tuple of (content, completion_tokens, finish_reason).

        Raises:
            NoMessageError: If no message content found in response.
        """
        if response.candidates and response.usage_metadata:
            candidate: Candidate = response.candidates[0]
            content: str = "".join(candidate.content.parts).strip()
            completion_tokens: int = candidate.token_count
            finish_reason: FinishReason = candidate.finish_reason
            total_tokens: int = response.usage_metadata.total_token_count
            self.update_rate_limit_dict(total_tokens)
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
        """Post-process the response received from the Gemini API.

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

        if finish_reason == FinishReason.MAX_TOKENS:
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
