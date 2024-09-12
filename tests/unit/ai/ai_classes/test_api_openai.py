import ast
import os
from unittest.mock import patch, MagicMock

import pytest
import openai

import lorebinders._managers as managers
from lorebinders.ai.ai_classes.api_openai import OpenaiAPI
from lorebinders.ai.api_error_handler import APIErrorHandler
from lorebinders.ai.exceptions import KeyNotFoundError, NoMessageError

# Fixtures
class MockSystemExit(Exception):
    pass

@pytest.fixture
def mock_email_handler() -> MagicMock:
    return MagicMock(spec=managers.EmailManager)

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
    with patch("lorebinders.ai.ai_classes.api_openai.OpenaiAPI._initialize_client"):
        with patch("lorebinders.ai.ai_classes.api_openai.tiktoken.get_encoding", return_value = MagicMock()):
            api = OpenaiAPI(mock_email_handler)
            api.client = MagicMock()
            api.error_handler = mock_error_handler
            return api

@pytest.fixture
def mock_model():
    mock = MagicMock()
    mock.name = "test_model"
    mock.rate_limit = 1000
    mock.api_model = "test-model"
    return mock

@pytest.fixture
def mock_rate_limit_manager():
    manager = MagicMock(spec=managers.RateLimitManager)
    manager.read = MagicMock(return_value = {"minute": 0, "tokens_used": 0})
    return manager

@pytest.fixture
def mock_rate_limit(mock_rate_limit_manager):
    with patch("lorebinders.ai.rate_limit.RateLimit.__init__", return_value=None):
        rate_limiter = MagicMock()
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
    return {
        "api_model":"test-model",
        "prompt":"What is the meaning of life?",
        "role_script":"You are a helpful assistant.",
        "temperature":0.7,
        "max_tokens":50,
    }

@pytest.fixture
def mock_modified_payload():
    return {
        "api_model":"test-model",
        "prompt":"What is the meaning of life?",
        "role_script":"You are a helpful assistant.",
        "temperature":0.7,
        "max_tokens":500,
    }

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

@pytest.fixture
def mock_full_json_response_dict():
    return {"test": {"test1": "value1", "test2": "value2"}, "test3": {"test4": "value4", "test5": "value5"}}

### Tests for OpenaiAPI

# tests for __init__
@patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"})
@patch("lorebinders.ai.ai_classes.api_openai.OpenAI")
@patch("lorebinders.ai.ai_classes.api_openai.tiktoken.get_encoding")
@patch("lorebinders.ai.ai_classes.api_openai.APIErrorHandler")
def test_openai_api_init_with_key(mock_error_handler, mock_get_encoding, mock_openai, mock_email_handler):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    api = OpenaiAPI(mock_email_handler)

    mock_openai.assert_called_once_with(api_key="test_api_key")
    assert api.client == mock_client
    mock_get_encoding.assert_called_once()
    mock_error_handler.assert_called_once()

@patch.dict("os.environ", {}, clear=True)
@patch("lorebinders.ai.ai_classes.api_openai.OpenaiAPI._error_handle")
@patch("lorebinders.ai.ai_classes.api_openai.tiktoken.get_encoding")
def test_openai_api_init_key_error(mock_get_encoding, mock_error_handle, mock_email_handler):
    OpenaiAPI(mock_email_handler)

    mock_error_handle.assert_called_once()
    args, _ = mock_error_handle.call_args
    assert isinstance(args[0], KeyNotFoundError)
    assert str(args[0]) == "OPENAI_API_KEY environment variable not set"

    mock_get_encoding.assert_called_once_with("cl100k_base")

# tests for _set_unresolvable_errors
def test_openai_api_set_unresolvable_errors(mock_openai_api):
    assert mock_openai_api.unresolvable_errors == (
        KeyNotFoundError,
        openai.BadRequestError,
        openai.AuthenticationError,
        openai.NotFoundError,
        openai.PermissionDeniedError,
        openai.UnprocessableEntityError,
    )

# tests for create_message_payload
@patch.object(OpenaiAPI, "_add_assistant_message")
@patch.object(OpenaiAPI, "_count_tokens")
def test_openai_api_create_message_payload_with_assistant_message(mock_count_tokens, mock_add_assistant_message, mock_openai_api):
    role_script = "Test role script"
    prompt = "Test prompt"
    assistant_message = "Test assistant message"
    expected_messages = [
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
    mock_count_tokens.return_value = 10
    mock_add_assistant_message.return_value = expected_messages
    messages, input_tokens = mock_openai_api.create_message_payload(
        role_script, prompt, assistant_message
    )
    assert messages == expected_messages
    assert input_tokens == 10
    mock_count_tokens.assert_called_once_with("Test role scriptTest promptTest assistant messagePlease continue from the exact point you left off without any commentary")
    mock_add_assistant_message.assert_called_once()


@patch.object(OpenaiAPI, "_count_tokens")
def test_openai_api_create_message_payload_without_assistant_message(
    mock_count_tokens, mock_openai_api
):
    role_script = "Test role script"
    prompt = "Test prompt"
    expected_messages = [
        {"role": "system", "content": "Test role script"},
        {"role": "user", "content": "Test prompt"},
    ]
    mock_count_tokens.return_value = 10
    messages, input_tokens = mock_openai_api.create_message_payload(
        role_script, prompt
    )
    assert messages == expected_messages
    assert input_tokens == 10
    mock_count_tokens.assert_called_once_with("Test role scriptTest prompt")

# tests for _add_assistant_message
def test_openai_api_add_assistant_message(mock_openai_api):
    messages = [
        {"role": "system", "content": "Test role script"},
        {"role": "user", "content": "Test prompt"},
    ]
    assistant_message = "Test assistant message"
    result = mock_openai_api._add_assistant_message(messages, assistant_message)
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

# tests for _count_tokens
def test_openai_api_count_tokens(mock_openai_api):
    text = "Test text"
    mock_openai_api.tokenizer.encode.return_value = [1, 2, 3, 4]

    result = mock_openai_api._count_tokens(text)

    assert result == 4
    mock_openai_api.tokenizer.encode.assert_called_once_with(text)

# tests for set_model from superclass
def test_openai_api_set_model(mock_openai_api, mock_model, mock_rate_limit, mock_rate_limit_manager):
    mock_model.api_model = "test_model"
    mock_model.rate_limit = 1000

    with patch("lorebinders.ai.rate_limit.RateLimit", return_value=mock_rate_limit):
        mock_openai_api.set_model(mock_model, mock_rate_limit_manager)

        assert mock_openai_api.model == mock_model
        assert mock_openai_api.api_model == "test_model"
        assert mock_rate_limit.rate_limit_dict == {"minute": 0, "tokens_used": 0}

# tests for call_api
@patch.object(OpenaiAPI, "_make_api_call", return_value="Processed Response")
def test_openai_api_call_api_success(
    mock_make_api_call,
    mock_openai_api,
    mock_payload,
):
    api_payload = mock_payload

    response = mock_openai_api.call_api(api_payload)

    mock_make_api_call.assert_called_once()
    assert response == "Processed Response"

@patch.object(OpenaiAPI, "_make_api_call")
def test_openai_api_call_api_unresolvable_error_handling(
    mock_make_api_call,
    mock_openai_api,
    mock_payload,
):
    api_payload = mock_payload
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
    api_payload = mock_payload
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

# tests for _make_api_call
@patch.object(OpenaiAPI, "_enforce_rate_limit")
@patch.object(OpenaiAPI, "process_response", return_value = "Mock Content")
@patch.object(OpenaiAPI, attribute="preprocess_response", return_value = ("Mock Content", 5, "Stop"))
def test_make_api_call(
    mock_preprocess_response,
    mock_process_response, mock_enforce_rate_limit,
    mock_openai_api_with_rate_limit,
    mock_payload
):
    api_payload = mock_payload
    input_tokens = 24
    json_response = False
    retry_count = 0
    assistant_message = None

    messages = [
        {"role": "system", "content": mock_payload["role_script"]},
        {"role": "user", "content": mock_payload["prompt"]}
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


    result = mock_openai_api_with_rate_limit._make_api_call(
        api_payload, messages, input_tokens, json_response, retry_count, assistant_message
    )

    mock_enforce_rate_limit.assert_called_once_with(
        input_tokens,
        mock_payload["max_tokens"]
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

# tests for preprocess_response
def test_openai_api_preprocess_response_success(mock_openai_api_with_rate_limit):
    response = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )

    with patch.object(mock_openai_api_with_rate_limit.rate_limiter, 'update_tokens_used') as mock_update_tokens:
        content, completion_tokens, finish_reason = mock_openai_api_with_rate_limit.preprocess_response(response)

    assert content == "Mock Content"
    assert completion_tokens == 5
    assert finish_reason == "stop"
    mock_update_tokens.assert_called_once_with(10)

def test_openai_api_preprocess_response_no_message_content(mock_openai_api):
    response = MagicMock(choices=[MagicMock(message=MagicMock(content=None))])
    with pytest.raises(NoMessageError):
        mock_openai_api.preprocess_response(response)

#tests for process_response
def test_openai_api_process_response_with_assistant_message(
    mock_openai_api, mock_payload
):
    api_payload = mock_payload
    assistant_message = "Test assistant message"
    response = mock_openai_api.process_response(
        content_tuple=("Mock Content", 5, "stop"),
        api_payload=api_payload,
        retry_count=0,
        json_response=False,
        assistant_message=assistant_message
    )
    assert response == "Test assistant messageMock Content"

@patch.object(OpenaiAPI, "_combine_answer")
def test_openai_api_process_response_with_assistant_message_json(
    mock_combine_answer, mock_openai_api, mock_payload, mock_partial_json_response_complete, mock_json_second_response, mock_full_json_response
):
    api_payload = mock_payload
    assistant_message = mock_partial_json_response_complete
    mock_combine_answer.return_value = mock_full_json_response
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
    api_payload = mock_payload
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
    api_payload = mock_payload
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
    mock__handle_length_limit, mock_openai_api, mock_payload, mock_partial_json_response_complete, mock_full_json_response_dict
):
    mock__handle_length_limit.return_value = mock_full_json_response_dict
    api_payload = mock_payload
    response = mock_openai_api.process_response(
        content_tuple=(mock_partial_json_response_complete, 30, "length"),
        api_payload=api_payload,
        retry_count=0,
        json_response=True
    )
    assert response == mock_full_json_response_dict
    mock__handle_length_limit.assert_called_once_with(
        answer=mock_partial_json_response_complete,
        api_payload=api_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=30
    )

#tests for _combine_answer
def test_openai_api_combine_answer_text(mock_openai_api):
    assistant_message = "Test assistant message"
    content = "Mock Content"
    combined_answer = mock_openai_api._combine_answer(
        assistant_message, content, False
    )
    assert combined_answer == "Test assistant messageMock Content"

@patch("lorebinders.ai.ai_classes.api_openai.merge_json")
@patch("lorebinders.ai.ai_classes.api_openai.repair_json_str")
def test_openai_api_combine_answer_json_calls_merge_json(mock_repair_json_str, mock_merge_json, mock_openai_api,mock_partial_json_response_complete, mock_json_second_response, mock_full_json_response):
    assistant_message = mock_partial_json_response_complete
    content = mock_json_second_response
    mock_merge_json.return_value = mock_full_json_response
    removed_character = content[1:]

    combined_answer = mock_openai_api._combine_answer(
        assistant_message, content, True
    )

    assert combined_answer == mock_full_json_response
    mock_merge_json.assert_called_once_with(assistant_message, removed_character)
    mock_repair_json_str.assert_not_called()

@patch("lorebinders.ai.ai_classes.api_openai.merge_json")
@patch("lorebinders.ai.ai_classes.api_openai.repair_json_str")
def test_openai_api_combine_answer_json_calls_repair_json_str(mock_repair_json_str, mock_merge_json, mock_openai_api, mock_partial_json_response_incomplete, mock_full_json_response):
    assistant_message = mock_partial_json_response_incomplete
    content = mock_full_json_response
    mock_merge_json.return_value = ""
    mock_repair_json_str.return_value = mock_full_json_response
    removed_character = content[1:]

    combined_answer = mock_openai_api._combine_answer(
        assistant_message, content, True
    )

    assert combined_answer == mock_full_json_response
    mock_repair_json_str.assert_called_once_with(assistant_message + removed_character)
    mock_merge_json.assert_called_once_with(assistant_message, removed_character)

#tests for _handle_length_limit
@patch.object(OpenaiAPI, "call_api")
@patch.object(OpenaiAPI, "modify_payload")
@patch("lorebinders.ai.ai_classes.api_openai.logger")
def test_openai_api_handle_length_limit(mock_logger, mock_modify_payload, mock_call_api,mock_modified_payload,  mock_openai_api, mock_payload):
    answer = "Test answer"
    mock_call_api.return_value = "Modified Response"
    mock_modify_payload.return_value = mock_modified_payload

    response = mock_openai_api._handle_length_limit(
        answer, mock_payload, 0, False, 40
    )

    assert response == "Modified Response"
    mock_logger.warning.assert_called_once_with(
        "Max tokens exceeded.\nUsed 40 of 50"
    )
    mock_call_api.assert_called_once_with(api_payload=mock_modified_payload, json_response=False, retry_count=0, assistant_message=answer)

@patch.object(OpenaiAPI, "call_api")
@patch.object(OpenaiAPI, "modify_payload")
@patch("lorebinders.ai.ai_classes.api_openai.logger")
def test_openai_api_handle_length_limit_json_complete_object(mock_logger, mock_modify_payload, mock_call_api, mock_openai_api, mock_payload, mock_modified_payload):
    initial_answer = '{"test": {"test1": "value1", "test2": "value2"}, "test3":'
    completion_tokens = 40

    mock_modify_payload.return_value = mock_modified_payload

    expected_response = '{"test": {"test1": "value1", "test2": "value2"}, "test3": {"test4": "value4", "test5": "value5"}}'
    mock_call_api.return_value = expected_response

    result = mock_openai_api._handle_length_limit(
        answer=initial_answer,
        api_payload=mock_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=completion_tokens
    )

    assert result == expected_response
    mock_logger.warning.assert_called_once_with(
        "Max tokens exceeded.\nUsed 40 of 50"
    )
    mock_call_api.assert_called_once_with(
        api_payload=mock_modified_payload, json_response=True, retry_count=0, assistant_message='{"test": {"test1": "value1", "test2": "value2"}'
    )

@patch.object(OpenaiAPI, "call_api")
@patch.object(OpenaiAPI, "modify_payload")
@patch("lorebinders.ai.ai_classes.api_openai.logger")
def test_openai_api_handle_length_limit_json_incomplete_object(mock_logger, mock_modify_payload, mock_call_api, mock_openai_api, mock_payload, mock_modified_payload, mock_partial_json_response_incomplete, mock_full_json_response):
    initial_answer = mock_partial_json_response_incomplete
    completion_tokens = 40

    mock_modify_payload.return_value = mock_modified_payload

    mock_call_api.return_value = mock_full_json_response

    result = mock_openai_api._handle_length_limit(
        answer=initial_answer,
        api_payload=mock_payload,
        retry_count=0,
        json_response=True,
        completion_tokens=completion_tokens
    )

    assert result == mock_full_json_response
    mock_logger.warning.assert_called_once_with(
        "Max tokens exceeded.\nUsed 40 of 50"
    )
    mock_call_api.assert_called_once_with(
        api_payload=mock_modified_payload, json_response=True, retry_count=0, assistant_message=""
    )
