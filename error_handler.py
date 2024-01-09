import logging

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
    error_context = f"Processing file: {cls.current_file if cls.current_file else 'No file info available'}"
    error_message = f"Error: {e}. Context: {error_context}"
    logging.critical(error_message)
    email_error(error_message)
    exit(1)
