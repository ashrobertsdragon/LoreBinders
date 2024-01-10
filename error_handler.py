import inspect
import logging
import traceback

from send_email import email_error


logging.basicConfig(filename="critial_error.log", level=logging.CRITICAL, 
                    format='%(asctime)s %(levelname)s:%(message)s')

class ErrorHandler:
  current_file = None

  @classmethod
  def set_current_file(cls, file):
    cls.current_file = file

  @classmethod
  def kill_app(cls, e: Exception):
    stack_info = traceback.format_exc()
    frame = inspect.currentframe().f_back.f_back
    file_name = frame.f_code.co_filename
    line_no = frame.f_lineno
    function_name = frame.f_code.co_name

    function_details = f"Error in {function_name} at line {line_no} in {file_name}:"
    file_details = f"File path: {cls.current_file if cls.current_file else 'No file info available'}"
    traceback_message = f"{function_details}\nStack Trace:\n{stack_info}"
    error_message = f"Error: {e}.\n{traceback_message}\n for LoreBinder in {file_details} "
    logging.critical(error_message)
    email_error(error_message)
    exit(1)
