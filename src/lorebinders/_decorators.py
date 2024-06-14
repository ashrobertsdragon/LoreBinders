from functools import wraps
from typing import Callable


def required_string(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        input_type = func.__name__.replace("input_", "")
        while True:
            result = func(*args, **kwargs)
            if isinstance(result, str) and result.strip():
                return result
            else:
                print(f"{input_type} is required.")

    return wrapper
