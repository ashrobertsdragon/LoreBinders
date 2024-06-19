import inspect
import json
import logging
import time
import traceback
from typing import Tuple

from _managers import EmailManager, ErrorManager
from ai_classes.exceptions import MaxRetryError


class APIErrorHandler(ErrorManager):
    """ """

    def __init__(
        self, email_manager: EmailManager, unresolvable_errors: Tuple
    ) -> None:
        self.email = email_manager
        self.unresolvable_errors = unresolvable_errors

    def _extract_error_info(self, e: Exception) -> Tuple[int, str]:
        """Extracts error code and message from a potential API exception."""
        try:
            if response := getattr(e, "response", None):
                error_details = response.json().get("error", {})
        except (AttributeError, json.JSONDecodeError):
            error_details = {}
        return getattr(e, "status_code", 0), error_details.get(
            "message", "Unknown error"
        )

    def _is_unresolvable_error(
        self, e: Exception, error_code: int, error_message: str
    ) -> bool:
        """Checks if the error is unresolvable."""
        return (
            isinstance(e, self.unresolvable_errors)
            or error_code == 401
            or "exceeded your current quota" in error_message
        )

    def handle_error(self, e: Exception, retry_count: int = 0) -> int:
        error_code, error_message = self._extract_error_info(e)
        if self._is_unresolvable_error(e, error_code, error_message):
            end_app = UnresolvableErrorHandler()
            end_app.kill_app(e)
        else:
            retry_handler = RetryHandler()
            return retry_handler.increment_retry_count(retry_count)


class RetryHandler:
    def __init__(self) -> None:
        self.max_retries = 5

    def _calculate_sleep_time(self) -> int:
        """
        The function calculates the sleep time based on the retry count and a
        predefined maximum number of retries.
        """

        return (self.max_retries - self.retry_count) + (self.retry_count**2)

    def _sleep(self) -> None:
        """
        Calculates the sleep time based on the retry count,logs a warning
        message with the retry count and sleep time, and then sleeps for the
        calculated time.

        """

        sleep_time = self._calculate_sleep_time()
        logging.warning(
            f"Retry attempt #{self.retry_count} in {sleep_time} seconds."
        )
        time.sleep(sleep_time)

    def increment_retry_count(self, retry_count: int) -> int:
        """Handles resolvable errors with exponential backoff."""
        self.retry_count = retry_count
        try:
            self.retry_count += 1
            if self.retry_count == self.max_retries:
                raise MaxRetryError("Maximum retry count reached")
            self._sleep(retry_count)
            return self.retry_count
        except MaxRetryError as e:
            end_app = UnresolvableErrorHandler()
            end_app.kill_app(e)


class UnresolvableErrorHandler:
    def _get_frame_info(self) -> Tuple[str, str, str]:
        """
        Retrieve information about the exception frame, including the file
        name, line number, function name, and binder name if available.
        """

        frame = inspect.currentframe()
        file_name, function_name = "Unknown", "Unknown"

        binder_name = "Unknown"

        while frame is not None and binder_name == "Unknown":
            if (
                not frame.f_code.co_filename.endswith("error_handler.py")
                and file_name == "Unknown"
            ):
                file_name = frame.f_code.co_filename
                function_name = frame.f_code.co_name

            locals_ = frame.f_locals
            if "binder" in locals_:
                binder_name = str(locals_["binder"])

            frame = frame.f_back

        return binder_name, file_name, function_name

    def _build_error_msg(self, e: Exception) -> str:
        """
        Generate an error message with detailed information including the
        function name, line number, file name, stack trace, and timestamp.
        """

        binder, file_name, function_name = self._get_frame_info()

        function_details = f"Error in {function_name} in {file_name}:"
        stack_info = traceback.format_exc()
        traceback_message = f"{function_details}\nStack Trace:\n{stack_info}"
        return (
            f"Error: {e}.\n"
            f"{traceback_message}\n"
            f"for Binder {binder}\n"
            f"Timestamp: {time.ctime()}"
        )

    def kill_app(self, e: Exception) -> None:
        """_summary_

        Args:
            e (Exception): _description_
        """
        error_message = self._build_error_msg(e)
        logging.critical(error_message)
        self.email.error_email(error_message)
        exit(1)
