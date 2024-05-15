import inspect
import logging
import traceback


from _managers import ErrorManager, EmailManager
from _types import Logger, Book

class ErrorHandler(ErrorManager):

    def __init__(cls, book: Book, email_manager: EmailManager) -> None:
        cls.book_name = book.title
        cls.file_path = book.book_file
        cls.email: EmailManager = email_manager
        logger: Logger = logging.getLogger(cls.book_name)
        logger.setLevel(logging.CRITICAL)

        file_handler = logging.FileHandler('critical_error.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False

    @classmethod
    def kill_app(cls, e: Exception) -> None:
        stack_info = traceback.format_exc()
        frame = inspect.currentframe().f_back.f_back
        file_name = frame.f_code.co_filename
        line_no = frame.f_lineno
        function_name = frame.f_code.co_name

        function_details = f"Error in {function_name} at line {line_no} in {file_name}:"
        file_details = f"File path: {cls.book_file}"
        traceback_message = f"{function_details}\nStack Trace:\n{stack_info}"
        error_message = f"Error: {e}.\n{traceback_message}\n for Binder in {file_details} "
        logging.critical(error_message)
        cls.email.email_error(error_message)
        exit(1)
