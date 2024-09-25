from functools import wraps
from typing import Callable

from loguru import logger

from lorebinders.ai.exceptions import DatabaseOperationError


def required_string(
    func: Callable,
):
    """
    Ensures that the result is a non-empty string.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> str:
        input_type = func.__name__.replace("input_", "")
        while True:
            result = func(*args, **kwargs)
            if isinstance(result, str) and result.strip():
                return result
            else:
                print(f"{input_type} is required.")

    return wrapper


def log_db_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseOperationError as e:
            logger.exception(f"Error: {e}")
            raise

    return wrapper
