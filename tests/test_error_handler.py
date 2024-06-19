import pytest
from unittest.mock import patch, MagicMock

from src.lorebinders._types import EmailManager
from src.lorebinders.error_handler import (
    APIErrorHandler,
    RetryHandler,
    UnresolvableErrorHandler,
)
from src.lorebinders.ai_classes.exceptions import MaxRetryError


@pytest.fixture
def mock_email_manager():
    return MagicMock(spec=EmailManager)


@pytest.fixture
def api_error_handler(mock_email_manager):
    return APIErrorHandler(mock_email_manager, (MaxRetryError,))


@pytest.fixture
def mock_exception():
    mock_exception = Exception("Test Exception")
    mock_exception.response = MagicMock(
        status_code=400,
        json=lambda: {"error": {"message": "Test error message"}},
    )
    return mock_exception


def test_extract_error_info(api_error_handler, mock_exception):
    error_code, error_message = api_error_handler._extract_error_info(
        mock_exception
    )
    assert error_code == 400
    assert error_message == "Test error message"


def test_extract_error_info_no_response(api_error_handler):
    mock_exception = Exception("Test Exception")
    error_code, error_message = api_error_handler._extract_error_info(
        mock_exception
    )
    assert error_code == 0
    assert error_message == "Unknown error"


def test_is_unresolvable_error_max_retry_error(
    api_error_handler, mock_exception
):
    assert api_error_handler._is_unresolvable_error(
        mock_exception, 400, "Test error message"
    )


def test_is_unresolvable_error_unauthorized(api_error_handler, mock_exception):
    mock_exception.response.status_code = 401
    assert api_error_handler._is_unresolvable_error(
        mock_exception, 401, "Test error message"
    )


def test_is_unresolvable_error_quota_exceeded(
    api_error_handler, mock_exception
):
    mock_exception.response.json.return_value = {
        "error": {"message": "You have exceeded your current quota"}
    }
    assert api_error_handler._is_unresolvable_error(
        mock_exception, 400, "You have exceeded your current quota"
    )


def test_is_unresolvable_error_not_unresolvable(
    api_error_handler, mock_exception
):
    assert not api_error_handler._is_unresolvable_error(
        mock_exception, 404, "Test error message"
    )


@patch("time.sleep")
def test_retry_handler_increment_retry_count_success(
    mock_sleep, api_error_handler
):
    retry_count = api_error_handler.handle_error(
        Exception("Test Error"), retry_count=2
    )
    assert retry_count == 3
    mock_sleep.assert_called_once()


@patch("time.sleep")
def test_retry_handler_increment_retry_count_max_retries(
    mock_sleep, api_error_handler
):
    retry_handler = RetryHandler()
    retry_handler.max_retries = 2  # Set max retries to 2 for this test
    retry_count = api_error_handler.handle_error(
        Exception("Test Error"), retry_count=1
    )
    assert retry_count == 2
    mock_sleep.assert_called_once()


@patch("time.sleep")
def test_retry_handler_increment_retry_count_unresolvable_error(
    mock_sleep, api_error_handler
):
    with patch.object(
        api_error_handler, "_is_unresolvable_error", return_value=True
    ):
        retry_count = api_error_handler.handle_error(
            MaxRetryError("Test Error"), retry_count=0
        )
    assert retry_count == 0  # Retry count should not be incremented
    mock_sleep.assert_not_called()


@patch("time.sleep")
@patch.object(UnresolvableErrorHandler, "kill_app")
def test_unresolvable_error_handler_kill_app(
    mock_kill_app, mock_sleep, api_error_handler
):
    mock_exception = Exception("Test Exception")
    mock_exception.response.status_code = 401
    api_error_handler.handle_error(mock_exception, retry_count=0)
    mock_kill_app.assert_called_once()
    mock_sleep.assert_not_called()


@patch("time.sleep")
@patch.object(UnresolvableErrorHandler, "kill_app")
def test_unresolvable_error_handler_kill_app_quota_exceeded(
    mock_kill_app, mock_sleep, api_error_handler
):
    mock_exception = Exception("Test Exception")
    mock_exception.response.json.return_value = {
        "error": {"message": "You have exceeded your current quota"}
    }
    api_error_handler.handle_error(mock_exception, retry_count=0)
    mock_kill_app.assert_called_once()
    mock_sleep.assert_not_called()


@patch.object(UnresolvableErrorHandler, "_build_error_msg")
@patch.object(UnresolvableErrorHandler, "_get_frame_info")
def test_unresolvable_error_handler_build_error_msg(
    mock_get_frame_info, mock_build_error_msg, api_error_handler
):
    mock_get_frame_info.return_value = (
        "Test Binder",
        "test_file.py",
        "test_function",
    )
    mock_exception = Exception("Test Exception")
    api_error_handler.handle_error(mock_exception, retry_count=0)
    mock_build_error_msg.assert_called_once()


@patch.object(UnresolvableErrorHandler, "kill_app")
@patch.object(
    UnresolvableErrorHandler,
    "_build_error_msg",
    return_value="Test Error Message",
)
def test_unresolvable_error_handler_kill_app_calls_email(
    mock_build_error_msg, mock_kill_app, api_error_handler, mock_email_manager
):
    mock_exception = Exception("Test Exception")
    api_error_handler.handle_error(mock_exception, retry_count=0)
    mock_kill_app.assert_called_once()
    mock_email_manager.error_email.assert_called_once_with(
        "Test Error Message"
    )
