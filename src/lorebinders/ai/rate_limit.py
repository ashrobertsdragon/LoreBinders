import logging
import time

from lorebinders._managers import RateLimitManager


class RateLimit:
    def __init__(
        self,
        model_name: str,
        rate_limit: int,
        rate_handler: RateLimitManager,
    ) -> None:
        self.model_name = model_name
        self.rate_limit = rate_limit
        self._rate_handler = rate_handler
        self.read_rate_limit_dict()

    def cool_down(self):
        """
        Pause the application thread while the rate limit is in danger of
        being exceeded.
        """
        logging.warning("Rate limit in danger of being exceeded")
        sleep_time = 60 - (time.time() - self.minute)
        logging.info(f"Sleeping {sleep_time} seconds")
        time.sleep(sleep_time)
        self.reset_rate_limit_dict()

    def is_rate_limit_exceeded(
        self, input_tokens: int, max_tokens: int
    ) -> bool:
        """
        Check if the rate limit has been exceeded.

        Args:
            input_tokens (int): The number of tokens used in the API call.
            max_tokens (int): The maximum number of tokens allowed for the API
                call.
        """
        if self._new_minute():
            self.reset_rate_limit_dict()

        return self.tokens_used + input_tokens + max_tokens > self.rate_limit

    def read_rate_limit_dict(self) -> None:
        """
        Read the rate limit dictionary from the rate limit manager.
        """
        self.rate_limit_dict: dict = self._rate_handler.read(self.model_name)

    def reset_rate_limit_dict(self) -> None:
        """
        Reset the rate limit information and update the dictionary.
        """

        self._reset_minute()
        self._reset_tokens_used()
        self.update_rate_limit_dict()

    def update_rate_limit_dict(self) -> None:
        """
        Write the rate limit dictionary to the rate limit manager.
        """
        self._rate_handler.write(self.model_name, self.rate_limit_dict)

    def update_tokens_used(self, tokens: int) -> None:
        """
        Update the number of tokens used in the rate limit dictionary.
        """
        self.read_rate_limit_dict()
        self.rate_limit_dict["tokens_used"] += tokens
        self.update_rate_limit_dict()

    def _new_minute(self) -> bool:
        """
        Check if 60 seconds have passed since the rate limit dictionary was
        last updated.

        Returns:
            bool: True if it's a new minute, False otherwise.
        """
        return time.time() > self.minute + 60

    def _reset_minute(self) -> None:
        """Reset the minute in the rate limit dictionary."""
        self.rate_limit_dict["minute"] = time.time()

    def _reset_tokens_used(self) -> None:
        """Reset the tokens used in the rate limit dictionary."""
        self.rate_limit_dict["tokens_used"] = 0

    @property
    def minute(self) -> float:
        """Get the minute in the rate limit dictionary."""
        self.read_rate_limit_dict()
        return self.rate_limit_dict["minute"]

    @property
    def tokens_used(self) -> int:
        """Get the tokens used in the rate limit dictionary."""
        self.read_rate_limit_dict()
        return self.rate_limit_dict["tokens_used"]
