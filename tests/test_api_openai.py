import os
from unittest.mock import patch, MagicMock

import openai
import pytest
from openai import OpenAI

from src.lorebinders._managers import RateLimitManager, EmailManager
from src.lorebinders.error_handler import APIErrorHandler
from src.lorebinders.ai_classes.ai_factory import RateLimit
from src.lorebinders.ai_classes.api_openai import OpenaiAPI
from src.lorebinders.ai_classes.exceptions import (
    MaxRetryError,
    KeyNotFoundError,
    NoMessageError,
)


@pytest.fixture
def mock_rate_limit_manager():
    return MagicMock(spec=RateLimitManager)


@pytest.fixture
def mock_model():
    return MagicMock(model="test_model")


@pytest.fixture
def openai_api(mock_rate_limit_manager, mock_model):
    openai_api = OpenaiAPI()
    openai_api.client = MagicMock()
    openai_api.model = mock_model
    openai_api.model_name = mock_model.model
    openai_api.tokenizer = MagicMock()
    openai_api.rate_limiter = RateLimit(
        mock_model.model, mock_rate_limit_manager
    )
    openai_api.error_handler = APIErrorHandler(
        email_manager=MagicMock(spec=EmailManager),
        unresolvable_errors=(MaxRetryError,),
    )
    return openai_api


@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_openai_api_init(openai_api):
    assert isinstance(openai_api.client, OpenAI)
    assert openai_api.client.api_key == "test_api_key"


@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_openai_api_init_key_error(monkeypatch, openai_api):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(KeyNotFoundError):
        OpenaiAPI()


def test_openai_api_set_unresolvable_errors(openai_api):
    assert openai_api.unresolvable_errors == (
        openai.BadRequestError,
        openai.AuthenticationError,
        openai.NotFoundError,
        openai.PermissionDeniedError,
        openai.UnprocessableEntityError,
    )


def test_openai_api_create_message_payload_with_assistant_message(openai_api):
    role_script = "Test role script"
    prompt = "Test prompt"
    assistant_message = "Test assistant message"
    messages, input_tokens = openai_api.create_message_payload(
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
    openai_api._count_tokens.assert_called_once_with(
        "Test role script"
        "Test prompt"
        "Test assistant message"
        "Please continue from the exact point you left off without "
        "any commentary"
    )
    assert input_tokens == len(openai_api._count_tokens.return_value)


def test_openai_api_create_message_payload_without_assistant_message(
    openai_api,
):
    role_script = "Test role script"
    prompt = "Test prompt"
    messages, input_tokens = openai_api.create_message_payload(
        role_script, prompt
    )
    assert messages == [
        {"role": "system", "content": "Test role script"},
        {"role": "user", "content": "Test prompt"},
    ]
    openai_api._count_tokens.assert_called_once_with(
        "Test role scriptTest prompt"
    )
    assert input_tokens == len(openai_api._count_tokens.return_value)


def test_openai_api_count_tokens(openai_api):
    text = "Test text"
    tokens = openai_api._count_tokens(text)
    openai_api.tokenizer.encode.assert_called_once_with(text)
    assert tokens == len(openai_api.tokenizer.encode.return_value)


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
@patch.object(OpenaiAPI, "process_response", return_value="Processed Response")
def test_openai_api_call_api_success(
    mock_process_response,
    mock_preprocess_response,
    mock_create,
    openai_api,
    mock_payload,
    mock_ai_implementation,
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
    response = openai_api.call_api(api_payload)
    mock_create.assert_called_once()
    mock_preprocess_response.assert_called_once_with(mock_create.return_value)
    mock_process_response.assert_called_once_with(
        ("Mock Content", 5, "stop"), None, api_payload, 0, False
    )
    assert response == "Processed Response"


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
@patch.object(OpenaiAPI, "process_response", return_value="Processed Response")
def test_openai_api_call_api_error_handling(
    mock_process_response,
    mock_preprocess_response,
    mock_create,
    openai_api,
    mock_payload,
    mock_ai_implementation,
):
    api_payload = mock_payload.model_dump()
    mock_create.side_effect = openai.BadRequestError("Test Error")
    response = openai_api.call_api(api_payload)
    mock_create.assert_called_once()
    mock_preprocess_response.assert_not_called()
    mock_process_response.assert_not_called()
    assert response == "Processed Response"
    openai_api.error_handler.handle_error.assert_called_once_with(
        openai.BadRequestError("Test Error"), 0
    )


def test_openai_api_preprocess_response_success(openai_api):
    response = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    content, completion_tokens, finish_reason = openai_api.preprocess_response(
        response
    )
    assert content == "Mock Content"
    assert completion_tokens == 5
    assert finish_reason == "stop"
    openai_api.update_rate_limit_data.assert_called_once_with(10)


def test_openai_api_preprocess_response_no_message_content(openai_api):
    response = MagicMock(choices=[MagicMock(message=MagicMock(content=None))])
    with pytest.raises(NoMessageError):
        openai_api.preprocess_response(response)


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_with_assistant_message(
    mock_preprocess_response, mock_create, openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    assistant_message = "Test assistant message"
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    response = openai_api.process_response(
        ("Mock Content", 5, "stop"), assistant_message, api_payload, 0, False
    )
    assert response == "Test assistant messageMock Content"


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_with_assistant_message_json(
    mock_preprocess_response, mock_create, openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    assistant_message = '{"test": "value"}'
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"), finish_reason="stop"
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    response = openai_api.process_response(
        ("Mock Content", 5, "stop"), assistant_message, api_payload, 0, True
    )
    assert response == '{"test": "value", "Mock Content"}'


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_without_assistant_message(
    mock_preprocess_response, mock_create, openai_api, mock_payload
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
    response = openai_api.process_response(
        ("Mock Content", 5, "stop"), None, api_payload, 0, False
    )
    assert response == "Mock Content"


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_length_limit(
    mock_preprocess_response, mock_create, openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"),
                finish_reason="length",
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    response = openai_api.process_response(
        ("Mock Content", 5, "length"), None, api_payload, 0, False
    )
    assert response == "Mock Content"
    openai_api.call_api.assert_called_once_with(
        api_payload, False, 0, "Mock Content"
    )


@patch("openai.ChatCompletion.create")
@patch.object(
    OpenaiAPI, "preprocess_response", return_value=("Mock Content", 10, "stop")
)
def test_openai_api_process_response_length_limit_json(
    mock_preprocess_response, mock_create, openai_api, mock_payload
):
    api_payload = mock_payload.model_dump()
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Mock Content"),
                finish_reason="length",
            )
        ],
        usage=MagicMock(total_tokens=10, completion_tokens=5),
    )
    response = openai_api.process_response(
        ("Mock Content", 5, "length"), None, api_payload, 0, True
    )
    assert response == "Mock Content"
    openai_api.call_api.assert_called_once_with(api_payload, True, 0, "")


def test_openai_api_combine_answer_text(openai_api):
    assistant_message = "Test assistant message"
    content = "Mock Content"
    combined_answer = openai_api._combine_answer(
        assistant_message, content, False
    )
    assert combined_answer == "Test assistant messageMock Content"


def test_openai_api_combine_answer_json(openai_api):
    assistant_message = '{"test": "value"}'
    content = "Mock Content"
    combined_answer = openai_api._combine_answer(
        assistant_message, content, True
    )
    assert combined_answer == '{"test": "value", "Mock Content"}'


def test_openai_api_handle_length_limit(openai_api, mock_payload):
    api_payload = mock_payload.model_dump()
    answer = "Test answer"
    openai_api.call_api.return_value = "Modified Response"
    response = openai_api._handle_length_limit(
        answer, api_payload, 0, False, 10
    )
    assert response == "Modified Response"
    openai_api.call_api.assert_called_once_with(api_payload, False, 0, answer)


def test_openai_api_handle_length_limit_json(openai_api, mock_payload):
    api_payload = mock_payload.model_dump()
    answer = '{"test": "value", "Mock Content"}'
    openai_api.call_api.return_value = "Modified Response"
    response = openai_api._handle_length_limit(
        answer, api_payload, 0, True, 10
    )
    assert response == "Modified Response"
    openai_api.call_api.assert_called_once_with(
        api_payload, True, 0, '{"test": "value"}'
    )
