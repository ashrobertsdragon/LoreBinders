import pytest
from unittest.mock import patch, Mock, MagicMock

from lorebinders.ai.api_error_handler import (
    APIErrorHandler,
    RetryHandler,
    UnresolvableErrorHandler,
)
from lorebinders.ai.exceptions import MaxRetryError

# fixtures
@pytest.fixture
def mock_email_manager():
    return MagicMock()

@pytest.fixture
def mock_exception():
    mock_exception = MagicMock()
    mock_exception.response = MagicMock(
        status_code=400,
        json=lambda: {"error": {"message": "Test error message"}},
    )
    return mock_exception

@pytest.fixture
def api_error_handler(mock_email_manager):
    return APIErrorHandler(mock_email_manager, (MaxRetryError,))

@pytest.fixture
def retry_handler(mock_email_manager):
    return RetryHandler(mock_email_manager)

@pytest.fixture
def unresolvable_error_handler(mock_email_manager):
    return UnresolvableErrorHandler(mock_email_manager)

# APIErrorHandler tests
def test_api_error_handler_init(mock_email_manager):
    api_error_handler = APIErrorHandler(mock_email_manager, (MaxRetryError,))
    assert api_error_handler.email == mock_email_manager
    assert api_error_handler.unresolvable_errors == (MaxRetryError,)

def test_api_error_handler_extract_error_info(api_error_handler, mock_exception):
    error_code, error_message = api_error_handler._extract_error_info(
        mock_exception
    )
    assert error_code == 400
    assert error_message == "Test error message"


def test_api_error_handler_extract_error_info_no_response(api_error_handler):
    mock_exception = Exception("Test Exception")
    error_code, error_message = api_error_handler._extract_error_info(
        mock_exception
    )
    assert error_code == 0
    assert error_message == "Unknown error"

def test_api_error_handler_is_unresolvable_error_unauthorized(api_error_handler, mock_exception):
    mock_exception.response.status_code = 401
    assert api_error_handler._is_unresolvable_error(
        mock_exception, 401, "Test error message"
    )

def test_api_error_handler_is_unresolvable_error_not_unresolvable(
    api_error_handler, mock_exception
):
    assert not api_error_handler._is_unresolvable_error(
        mock_exception, 404, "Test error message"
    )

@patch("lorebinders.ai.api_error_handler.UnresolvableErrorHandler")
@patch("lorebinders.ai.api_error_handler.RetryHandler")
@patch.object(APIErrorHandler, "_is_unresolvable_error", return_value=True)
@patch.object(APIErrorHandler, "_extract_error_info", return_value=(401, "Test error message"))
def test_api_error_handler_handle_error_unresolvable(mock_extract_error_info, mock_is_unresolvable_error, MockRetryHandler, MockUnresolvableErrorHandler, api_error_handler):
    mock_error = MagicMock(Exception("Test error message"))
    mock_error.error_code = 401
    retry_count = 0

    mock_end_app = MockUnresolvableErrorHandler.return_value
    mock_end_app.kill_app = MagicMock()
    retry_handler = MagicMock()
    MockRetryHandler.return_value = retry_handler
    MockRetryHandler.return_value.increment_retry_count.return_value = 0  # Not actually needed for this test

    api_error_handler.handle_error(mock_error, retry_count)

    mock_extract_error_info.assert_called_once_with(mock_error)
    mock_is_unresolvable_error.assert_called_once_with(mock_error, 401, "Test error message")
    MockUnresolvableErrorHandler.assert_called_once_with(api_error_handler.email)
    mock_end_app.kill_app.assert_called_once_with(mock_error)

@patch("lorebinders.ai.api_error_handler.UnresolvableErrorHandler")
@patch("lorebinders.ai.api_error_handler.RetryHandler")
@patch.object(APIErrorHandler, "_is_unresolvable_error", return_value=False)
@patch.object(APIErrorHandler, "_extract_error_info", return_value=(400, "Test error message"))
def test_api_error_handler_handle_error_increment_retry_count(mock_extract_error_info, mock_is_unresolvable_error, MockRetryHandler, MockUnresolvableErrorHandler, api_error_handler):
    mock_error = MagicMock(Exception("Test error message"))
    mock_error.error_code = 400
    retry_count = 0

    mock_end_app = MockUnresolvableErrorHandler.return_value
    mock_end_app.kill_app = MagicMock()

    retry_handler = MagicMock()
    MockRetryHandler.return_value = retry_handler
    MockRetryHandler.return_value.increment_retry_count.return_value = 1

    result = api_error_handler.handle_error(mock_error, retry_count)

    assert result == 1
    mock_extract_error_info.assert_called_once_with(mock_error)
    MockRetryHandler.assert_called_once_with(api_error_handler.email)
    mock_is_unresolvable_error.assert_called_once_with(mock_error, 400, "Test error message")
    MockUnresolvableErrorHandler.assert_not_called()

# RetryHandler tests
def test_retry_handler_init(mock_email_manager):
    retry_handler = RetryHandler(mock_email_manager)
    assert retry_handler.email_handler == mock_email_manager
    assert retry_handler.max_retries == 5

@pytest.mark.parametrize(
    "max_retries, retry_count, expected",
    [
        (3, 1, (3 - 1) + (1**2)),  # 2 + 1 = 3
        (3, 2, (3 - 2) + (2**2)),  # 1 + 4 = 5
        (3, 3, (3 - 3) + (3**2)),  # 0 + 9 = 9
        (5, 1, (5 - 1) + (1**2)),  # 4 + 1 = 5
        (5, 2, (5 - 2) + (2**2)),  # 3 + 4 = 7
        (5, 3, (5 - 3) + (3**2)),  # 2 + 9 = 11
        (5, 4, (5 - 4) + (4**2)),  # 1 + 16 = 17
        (5, 5, (5 - 5) + (5**2)),  # 0 + 25 = 25
    ]
)
def test_retry_handler_calculate_sleep_time(retry_handler, max_retries, retry_count, expected):
    # sourcery skip: bin-op-identity
    retry_handler.max_retries = max_retries
    retry_handler.retry_count = retry_count
    result = retry_handler._calculate_sleep_time()
    assert result == expected

import pytest
from unittest.mock import patch, MagicMock

@patch("lorebinders.ai.api_error_handler.logger")
@patch("lorebinders.ai.api_error_handler.time.sleep")
@patch("lorebinders.ai.api_error_handler.RetryHandler._calculate_sleep_time")
def test_retry_handler_sleep(mock_calculate_sleep_time, mock_sleep, mock_logger, retry_handler):

    mock_calculate_sleep_time.return_value = 2
    retry_handler.retry_count = 3

    retry_handler._sleep()

    mock_calculate_sleep_time.assert_called_once()
    mock_logger.warning.assert_called_once_with("Retry attempt #3 in 2 seconds.")
    mock_sleep.assert_called_once_with(2)

@patch("lorebinders.ai.api_error_handler.UnresolvableErrorHandler")
@patch.object(RetryHandler, "_sleep")
def test_retry_handler_increment_retry_count_success(
    mock_sleep, MockUnresolvableErrorHandler, retry_handler
):

    mock_kill_app = Mock()
    MockUnresolvableErrorHandler.return_value.kill_app = mock_kill_app

    retry_count = retry_handler.increment_retry_count(2)

    assert retry_count == 3
    mock_sleep.assert_called_once()
    MockUnresolvableErrorHandler.assert_not_called()

@patch("lorebinders.ai.api_error_handler.UnresolvableErrorHandler")
@patch.object(RetryHandler, "_sleep")
def test_retry_handler_increment_retry_count_max_retries(mock_sleep,MockUnresolvableErrorHandler, retry_handler):
    mock_kill_app = Mock()
    MockUnresolvableErrorHandler.return_value.kill_app = mock_kill_app

    retry_handler.increment_retry_count(4)

    MockUnresolvableErrorHandler.assert_called_once()
    mock_kill_app.assert_called_once()
    mock_sleep.assert_not_called()

# UnresolvableErrorHandler tests
def test_unresolvable_error_handler_init(mock_email_manager):
    unresolvable_error_handler = UnresolvableErrorHandler(mock_email_manager)
    assert unresolvable_error_handler.email == mock_email_manager


@patch("inspect.currentframe")
def test_get_frame_info_flat_frame( mock_currentframe, unresolvable_error_handler):

    mock_frame = Mock()
    mock_frame.f_code.co_filename = "test_file.py"
    mock_frame.f_code.co_name = "test_function"
    mock_frame.f_locals = {"book": "test_book"}
    mock_frame.f_back = None
    mock_currentframe.return_value = mock_frame

    book_name, file_name, function_name = unresolvable_error_handler._get_frame_info()

    assert book_name == "'test_book'"
    assert file_name == "test_file.py"
    assert function_name == "test_function"

@patch("inspect.currentframe")
def test_get_frame_info_nested_frame(mock_currentframe, unresolvable_error_handler):

    mock_frame_level_1 = Mock()
    mock_frame_level_1.f_code.co_filename = "level_1.py"
    mock_frame_level_1.f_code.co_name = "function_1"
    mock_frame_level_1.f_back = None

    mock_frame_level_2 = Mock()
    mock_frame_level_2.f_code.co_filename = "level_2.py"
    mock_frame_level_2.f_code.co_name = "function_2"
    mock_frame_level_2.f_locals = {"book": "test_book"}
    mock_frame_level_2.f_back = mock_frame_level_1

    mock_frame_level_3 = Mock()
    mock_frame_level_3.f_code.co_filename = "level_3.py"
    mock_frame_level_3.f_code.co_name = "function_3"
    mock_frame_level_3.f_locals = {}
    mock_frame_level_3.f_back = mock_frame_level_2


    mock_frame_level_4 = Mock()
    mock_frame_level_4.f_code.co_filename = "module_with_error.py"
    mock_frame_level_4.f_code.co_name = "function_with_error"
    mock_frame_level_4.f_locals = {}
    mock_frame_level_4.f_back = mock_frame_level_3

    mock_frame_level_5 = Mock()
    mock_frame_level_5.f_code.co_filename = "error_handler.py"
    mock_frame_level_5.f_code.co_name = "function_4"
    mock_frame_level_5.f_locals = {}
    mock_frame_level_5.f_back = mock_frame_level_4

    mock_currentframe.return_value = mock_frame_level_5

    book_name, file_name, function_name = unresolvable_error_handler._get_frame_info()

    assert book_name == "'test_book'"
    assert file_name == "module_with_error.py"
    assert function_name == "function_with_error"

@patch("lorebinders.ai.api_error_handler.save_data.save_progress")
def test_unresolvable_error_handler_save_data_success(mock_save_progress, unresolvable_error_handler):
    mock_save_progress.return_value = True

    result = unresolvable_error_handler._save_data("test_book")

    assert result == "Progress was saved."
    mock_save_progress.assert_called_once_with("test_book")


@patch("lorebinders.ai.api_error_handler.save_data.save_progress")
def test_unresolvable_error_handler_save_data_fail(mock_save_progress, unresolvable_error_handler):
    mock_save_progress.return_value = False

    result = unresolvable_error_handler._save_data("test_book")

    assert result == "Progress was not saved."
    mock_save_progress.assert_called_once_with("test_book")

@patch("lorebinders.ai.api_error_handler.traceback.format_exc", return_value="Mocked stack trace")
@patch("lorebinders.ai.api_error_handler.time.ctime", return_value="Mocked timestamp")
@patch.object(UnresolvableErrorHandler, "_get_frame_info", return_value=("test_book", "test_file.py", "test_function"))
@patch.object(UnresolvableErrorHandler, "_save_data", return_value="Progress was saved.")
def test_build_error_msg_generates_detailed_error_message(mock_save_data, mock_get_frame_info, mock_format_exc, mock_ctime, unresolvable_error_handler):

    exception = Exception("Test exception")
    result = unresolvable_error_handler._build_error_msg(exception)
    expected_message = (
        "Error: Test exception.\n"
        "Error in test_function in test_file.py:\n"
        "Stack Trace:\nMocked stack trace\n"
        "for Book test_book\n"
        "Progress was saved.\n"
        "Timestamp: Mocked timestamp"
    )
    assert result == expected_message
    mock_save_data.assert_called_once_with("test_book")
    mock_get_frame_info.assert_called_once()
    mock_ctime.assert_called_once()
    mock_format_exc.assert_called_once()

@patch("lorebinders.ai.api_error_handler.logger")
@patch.object(UnresolvableErrorHandler, "_build_error_msg", return_value="Detailed error message")
@patch("builtins.exit")
def test_kill_app_generates_detailed_error_message(mock_exit, mock_build_error_msg, mock_logger, unresolvable_error_handler):
    mock_error_email = Mock()
    unresolvable_error_handler.email.error_email = mock_error_email
    mock_exception = Exception("Test Exception")

    unresolvable_error_handler.kill_app(mock_exception)

    mock_exit.assert_called_once_with(1)
    mock_build_error_msg.assert_called_once_with(mock_exception)
    mock_logger.critical.assert_called_once_with("Detailed error message")
    mock_error_email.assert_called_once_with("Detailed error message")
