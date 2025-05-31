from collections.abc import Callable
from functools import wraps
from typing import Any

from loguru import logger

from lorebinders.ai.exceptions import DatabaseOperationError


def required_string(
    func: Callable[..., str],
) -> Callable[..., str]:
    """Ensures that the result is a non-empty string.

    Args:
        func: Function to wrap that should return a string.

    Returns:
        Wrapped function that ensures non-empty string result.
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


def log_db_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """Logs database errors and re-raises them.

    Args:
        func: Function to wrap for error logging.

    Returns:
        Wrapped function with database error logging.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except DatabaseOperationError as e:
            logger.exception(f"Error: {e}")
            raise

    return wrapper
