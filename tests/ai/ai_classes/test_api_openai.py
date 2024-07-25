import os
from unittest.mock import patch, MagicMock

import openai
import pytest
import tiktoken
from loguru import logger

from lorebinders._managers import EmailManager, RateLimitManager
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.ai_factory import Payload
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError
from lorebinders.ai.rate_limit import RateLimit
from lorebinders.ai.ai_classes.api_openai import OpenaiAPI

class MockSystemExit(Exception):
    pass

@pytest.fixture
def mock_email_handler() -> MagicMock:
    return MagicMock(spec=EmailManager)

@pytest.fixture
def mock_error_handler() -> MagicMock:
    def handle_error_side_effect(error, retry_count):
        if error.response.status_code == 400 or retry_count > 0:
            raise MockSystemExit
        return retry_count + 1

    handler = MagicMock(spec=APIErrorHandler)
    handler.handle_error.side_effect = handle_error_side_effect
    return handler

@pytest.fixture
def mock_openai_api(mock_email_handler, mock_error_handler) -> OpenaiAPI:
    api = OpenaiAPI(mock_email_handler)
    api.client = MagicMock()
    api.error_handler = mock_error_handler
    return api

@pytest.fixture
def tokenizer() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")

@pytest.fixture
def mock_model():
    mock = MagicMock()
    mock.name = "test_model"
    mock.rate_limit = 1000
    mock.api_model = "test-model"
    return mock

@pytest.fixture
def mock_rate_limit_manager():
    manager = MagicMock(spec=RateLimitManager)
    manager.read = MagicMock(return_value = {"minute": 0, "tokens_used": 0})
    return manager

@pytest.fixture
def mock_rate_limit(mock_rate_limit_manager):
    with patch('lorebinders.ai.rate_limit.RateLimit.__init__', return_value=None):
        rate_limiter = RateLimit()
        rate_limiter.name = "test_model"
        rate_limiter.rate_limit = 1000
        rate_limiter._rate_handler = mock_rate_limit_manager
        rate_limiter.rate_limit_dict = rate_limiter._rate_handler.read(rate_limiter.name)
        rate_limiter.read_rate_limit_dict = MagicMock()
    return rate_limiter


@pytest.fixture
def mock_openai_api_with_rate_limit(mock_openai_api, mock_rate_limit):
    mock_openai_api.rate_limiter = mock_rate_limit
    return mock_openai_api

@pytest.fixture
def mock_payload():
    return Payload(
        api_model="test-model",
        prompt="What is the meaning of life?",
        role_script="You are a helpful assistant.",
        temperature=0.7,
        max_tokens=50,
    )

@pytest.fixture
def mock_partial_json_response_complete():
    return '{"test": {"test1": "value1", "test2": "value2"}, "test3": {"test4": "value4'

@pytest.fixture
def mock_partial_json_response_incomplete():
    return '{"test": {"test1": "value1", "test2"'

@pytest.fixture
def mock_json_second_response():
    return '"test3": {"test4": "value4", "test5": "value5"}'

@pytest.fixture
def mock_full_json_response():
    return '{"test": {"test1": "value1", "test2": "value2"}, "test3": {"test4": "value4", "test5": "value5"}}'

@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_openai_api_init(mock_openai_api):
    assert isinstance(mock_openai_api.client, MagicMock)
    assert isinstance(mock_openai_api.error_handler, MagicMock)

@patch.dict('os.environ', {}, clear=True)
@patch('lorebinders.ai.ai_classes.api_openai.OpenaiAPI._error_handle')
def test_openai_api_init_key_error(mock_error_handle, mock_email_handler):
    OpenaiAPI(mock_email_handler)
    mock_error_handle.assert_called_once()

    args, _ = mock_error_handle.call_args
    assert isinstance(args[0], KeyNotFoundError)
    assert str(args[0]) == "OPENAI_API_KEY environment variable not set"

def test_openai_api_set_unresolvable_errors(mock_openai_api):
    assert mock_openai_api.unresolvable_errors == (
        KeyNotFoundError,
        openai.BadRequestError,
        openai.AuthenticationError,
        openai.NotFoundError,
        openai.PermissionDeniedError,
        openai.UnprocessableEntityError,
    )

def test_openai_api_create_message_payload_with_assistant_message(mock_openai_api, tokenizer):
    role_script = "Test role script"
    prompt = "Test prompt"
    assistant_message = "Test assistant message"
    messages, input_tokens = mock_openai_api.create_message_payload(
        role_script, prompt, assistant_message
    )
    assert messages == [
        {"role": "system", "content": "Test role script"},
        {"role": "user", "content": "Test prompt"},
        {"role": "assistant", "content": "Test assistant message"},
        {
            "role": "user",
            "content": (
                "Please continue from the exact point you left off without "
                "any commentary"
            ),
        },
    ]
    messages_text = (
        "Test role script"
        "Test prompt"
        "Test assistant message"
        "Please continue from the exact point you left off without "
        "any commentary"
    )
    assert input_tokens == len(tokenizer.encode(messages_text))


def test_openai_api_create_message_payload_without_assistant_message(
    mock_openai_api, tokenizer
):
    role_script = "Test role script"
    prompt = "Test prompt"
    messages, input_tokens = mock_openai_api.create_message_payload(
        role_script, prompt
    )
    assert messages == [
        {"role": "system", "content": "Test role script"},
        {"role": "user", "content": "Test prompt"},
    ]
    messages_text = "Test role scriptTest prompt"
    assert input_tokens == len(tokenizer.encode(messages_text))


def test_openai_api_count_tokens(mock_openai_api, tokenizer):
    text = "Test text"
    tokens = mock_openai_api._count_tokens(text)
    encoded_length = len(tokenizer.encode(text))
    assert tokens == encoded_length

def test_openai_api_preprocess_response_success(mock_openai_api_with_rate_limit):
    response = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    content, completion_tokens, finish_reason = mock_openai_api_with_rate_limit.preprocess_response(
        response
    )
    assert content == "Mock Content"
    assert completion_tokens == 5
    assert finish_reason == "stop"
    assert mock_openai_api_with_rate_limit.rate_limiter._rate_handler.write.called
    mock_openai_api_with_rate_limit.rate_limiter._rate_handler.write.assert_called_once()

def test_openai_api_preprocess_response_no_message_content(mock_openai_api):
    response = MagicMock(choices=[MagicMock(message=MagicMock(content=None))])
    with pytest.raises(NoMessageError):
        mock_openai_api.preprocess_response(response)

def test_openai_api_combine_answer_text(mock_openai_api):
    assistant_message = "Test assistant message"
    content = "Mock Content"
    combined_answer = mock_openai_api._combine_answer(
        assistant_message, content, False
    )
    assert combined_answer == "Test assistant messageMock Content"


def test_openai_api_combine_answer_json(mock_openai_api,mock_partial_json_response_complete, mock_json_second_response, mock_full_json_response):
    assistant_message = mock_partial_json_response_complete
    content = mock_json_second_response
    combined_answer = mock_openai_api._combine_answer(
        assistant_message, content, True
    )
    assert combined_answer == mock_full_json_response

def test_openai_api_set_model(mock_openai_api, mock_model, mock_rate_limit, mock_rate_limit_manager):
    mock_model.api_model = "test_model"
    mock_model.rate_limit = 1000

    with patch('lorebinders.ai.rate_limit.RateLimit', return_value=mock_rate_limit):
        mock_openai_api.set_model(mock_model, mock_rate_limit_manager)

        assert mock_openai_api.model == mock_model
        assert mock_openai_api.api_model == "test_model"
        assert mock_rate_limit.rate_limit_dict == {"minute": 0, "tokens_used": 0}

@patch.object(OpenaiAPI, '_make_api_call', return_value="Processed Response")
def test_openai_api_call_api_success(
    mock_make_api_call,
    mock_openai_api,
    mock_payload,
):
    api_payload = mock_payload.model_dump()

    response = mock_openai_api.call_api(api_payload)

    mock_make_api_call.assert_called_once()
    assert response == "Processed Response"

@patch.object(OpenaiAPI, "_make_api_call")
def test_openai_api_call_api_unresolvable_error_handling(
    mock_make_api_call,
    mock_openai_api,
    mock_payload,
):
    api_payload = mock_payload.model_dump()
    mock_make_api_call.side_effect = openai.BadRequestError(
        "Bad Request Test",
        response=MagicMock(status_code=400),
        body='{"code": 400}',
    )

    with pytest.raises(MockSystemExit):
        mock_openai_api.call_api(api_payload)
    mock_openai_api.error_handler.handle_error.assert_called_once()
    mock_openai_api.error_handler.handle_error.assert_called_once_with(
        mock_make_api_call.side_effect,
        0
    )

@patch.object(OpenaiAPI, "_make_api_call")
def test_call_api_with_retry(
    mock_make_api_call,
    mock_openai_api,
    mock_payload
):
    api_payload = mock_payload.model_dump()
    mock_make_api_call.side_effect = [
        openai.APIStatusError(
            "Service Unavailable",
            response=MagicMock(status_code=503),
            body='{"code": 503}'
        ),
        "Mock Content"
    ]
    result = mock_openai_api.call_api(api_payload, json_response=False, retry_count=0)
    assert result == "Mock Content"
    assert mock_make_api_call.call_count == 2

@patch.object(OpenaiAPI, "process_response", return_value = "Mock Content")
@patch.object(OpenaiAPI, attribute="preprocess_response", return_value = ("Mock Content", 5, "Stop"))
def test_make_api_call(
    mock_preprocess_response,
    mock_process_response,
    mock_openai_api_with_rate_limit,
    mock_payload
):
    api_payload = mock_payload.model_dump()
    input_tokens = 24
    json_response = False
    retry_count = 0
    assistant_message = None

    messages = [
        {"role": "system", "content": mock_payload.role_script},
        {"role": "user", "content": mock_payload.prompt}
    ]
    response_format = {"type": "text"}
    mock_chat_completion = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "Mock Content",
                    "role": "assistant"
                },
                "logprobs": None
            }
        ],
        "created": 1677664795,
        "id": "chatcmpl-7QyqpwdfhqwajicIEznoc6Q47XAyW",
        "model": "test-model",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 17,
            "prompt_tokens": 57,
            "total_tokens": 74
        }
    }
    mock_create = MagicMock(return_value=mock_chat_completion)
    mock_openai_api_with_rate_limit.client.chat.completions.create = mock_create

    logger.debug(f"Before _make_api_call: mock_create.call_count = {mock_create.call_count}")

    result = mock_openai_api_with_rate_limit._make_api_call(
        api_payload, messages, input_tokens, json_response, retry_count, assistant_message
    )

    mock_create.assert_called_once_with(
        model=mock_payload.api_model,
        response_format=response_format,
        messages=messages,
        max_tokens=mock_payload.max_tokens,
        temperature=mock_payload.temperature

    )
    mock_preprocess_response.assert_called_once_with(mock_chat_completion)
    mock_process_response.assert_called_once_with(
        content_tuple=("Mock Content", 5, "Stop"),
        api_payload=api_payload,
        retry_count=0,
        json_response=False,
        assistant_message=None
    )
    assert result == "Mock Content"


def test_openai_api_process_response_with_assistant_message(
    mock_openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    assistant_message = "Test assistant message"
    response = mock_openai_api.process_response(
        content_tuple=("Mock Content", 5, "stop"),
        api_payload=api_payload,
        retry_count=0,
        json_response=False,
        assistant_message=assistant_message
    )
    assert response == "Test assistant messageMock Content"


def test_openai_api_process_response_with_assistant_message_json(
    mock_openai_api, mock_payload, mock_partial_json_response_complete, mock_json_second_response, mock_full_json_response
):
    api_payload = mock_payload.model_dump()
    assistant_message = mock_partial_json_response_complete
    mock_openai_api._combine_answer = MagicMock(return_value=mock_json_second_response)
    response = mock_openai_api.process_response(
        content_tuple=(mock_json_second_response, 5, "stop"),
        api_payload=api_payload,
        retry_count=0,
        json_response=True,
        assistant_message=assistant_message,
    )
    mock_openai_api._combine_answer.assert_called_once_with(
        assistant_message=assistant_message, content=mock_json_second_response, json_response=True
    )
    assert response == mock_full_json_response


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_without_assistant_message(
    mock_create,mock_openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    response = mock_openai_api.process_response(
        content_tuple=("Mock Content", 5, "stop"),
         api_payload=api_payload,
         retry_count=0,
         json_response=False,
         assistant_message=None
    )
    assert response == mock_openai_api.process_response.return_value

@patch.object(
    OpenaiAPI, "_handle_length_limit", return_value=("Mock Content")
)
def test_openai_api_process_response_length_limit(
    mock__handle_length_limit, mock_openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    response = mock_openai_api.process_response(
        content_tuple=("Mock", 1, "length"),
        api_payload=api_payload,
        retry_count=0,
        json_response=False
    )
    assert response == "Mock Content"
    mock__handle_length_limit.assert_called_once_with(
        answer="Mock",
        api_payload=api_payload,
        retry_count=0,
        json_response=False,
        completion_tokens=1
    )

@patch.object(
    OpenaiAPI, "_handle_length_limit")
def test_openai_api_process_response_length_limit_json(
    mock__handle_length_limit, mock_openai_api, mock_payload, mock_partial_json_response_complete, mock_full_json_response
):
    mock__handle_length_limit.return_value = (mock_full_json_response, 5, "length")
    api_payload = mock_payload.model_dump()
    response = mock_openai_api.process_response(
        content_tuple=(mock_partial_json_response_complete, 30, "length"),
        api_payload=api_payload,
        retry_count=0,
        json_response=True
    )
    assert response == mock_full_json_response
    mock__handle_length_limit.assert_called_once_with(
        answer=mock_partial_json_response_complete,
        api_payload=api_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=30
    )

@patch.object(OpenaiAPI, 'call_api', return_value="Mocked Response")
def test_openai_api_handle_length_limit(mock_call_api, mock_openai_api, mock_payload):
    api_payload = mock_payload.model_dump()
    answer = "Test answer"
    mock_call_api.return_value = "Modified Response"
    response = mock_openai_api._handle_length_limit(
        answer, api_payload, 0, False, 10
    )
    assert response == "Modified Response"
    mock_call_api.assert_called_once_with(api_payload=api_payload, json_response=False, retry_count=0, assistant_message=answer)

@patch.object(OpenaiAPI, 'call_api')
def test_openai_api_handle_length_limit_json_complete_object(mock_call_api,mock_openai_api, mock_payload, mock_partial_json_response_complete, mock_json_second_response):
    initial_answer = mock_partial_json_response_complete
    completion_tokens = 40
    api_payload = mock_payload.model_dump()

    mock_call_api.return_value = mock_json_second_response

    last_complete = initial_answer.rfind("},")
    assistant_message = (
        initial_answer[: last_complete + 1] if last_complete > 0 else ""
    )
    result = mock_openai_api._handle_length_limit(
        answer=initial_answer,
        api_payload=api_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=completion_tokens
    )

    mock_call_api.assert_called_once_with(
        api_payload=api_payload, json_response=True, retry_count=0, assistant_message=assistant_message
    )

    assert last_complete == 46
    assert assistant_message == '{"test": {"test1": "value1", "test2": "value2"}'
    assert result == mock_json_second_response
    assert mock_openai_api.call_api.call_args[0][0]["max_tokens"] == 500

@patch.object(OpenaiAPI, 'call_api')
def test_openai_api_handle_length_limit_json_incomplete_object(mock_call_api, mock_openai_api, mock_payload, mock_partial_json_response_incomplete, mock_full_json_response):
    initial_answer = mock_partial_json_response_incomplete
    completion_tokens = 40
    api_payload = mock_payload.model_dump()

    mock_call_api.return_value = mock_full_json_response
    last_complete = initial_answer.rfind("},")
    assistant_message = (
        initial_answer[: last_complete + 1] if last_complete > 0 else ""
    )
    result = mock_openai_api._handle_length_limit(
        answer=initial_answer,
        api_payload=api_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=completion_tokens
    )

    mock_call_api.assert_called_once_with(
        api_payload=api_payload, json_response=True, retry_count=0, assistant_message=assistant_message
    )

    assert last_complete == -1
    assert assistant_message == ""
    assert result == mock_full_json_response
    assert mock_openai_api.call_api.call_args[0][0]["max_tokens"] == 500
