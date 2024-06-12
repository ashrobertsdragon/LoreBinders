import inspect
import logging
import traceback

from _managers import EmailManager, ErrorManager


class ErrorHandler(ErrorManager):
    def __init__(cls, email_manager: EmailManager) -> None:
        cls.email: EmailManager = email_manager

    @classmethod
    def kill_app(cls, e: Exception) -> None:
        stack_info = traceback.format_exc()
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
            if frame is not None:
                frame = frame.f_back
        if frame is not None:
            file_name = frame.f_code.co_filename
            line_no = frame.f_lineno
            function_name = frame.f_code.co_name

        function_details = (
            f"Error in {function_name} at line {line_no} in {file_name}:"
        )
        file_details = "File path: "
        traceback_message = f"{function_details}\nStack Trace:\n{stack_info}"
        error_message = (
            f"Error: {e}.\n{traceback_message}\n for Binder in {file_details} "
        )
        logging.critical(error_message)
        cls.email.error_email(error_message)
        exit(1)
