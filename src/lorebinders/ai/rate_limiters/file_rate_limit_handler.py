from __future__ import annotations

from lorebinders._managers import RateLimitManager
from lorebinders.file_handling import read_json_file, write_json_file


class FileRateLimitHandler(RateLimitManager):
    """File-based rate limit handler that stores data in JSON files."""

    def _filename(self, model_name: str) -> str:
        return f"{model_name}_rate_limit_data.json"

    def read(self, model_name: str) -> dict:
        """Read rate limit data from file.

        Args:
            model_name: Name of the model to read data for.

        Returns:
            Dictionary containing rate limit data.
        """
        filename = self._filename(model_name)
        return read_json_file(filename)

    def write(self, model_name: str, rate_limit_data: dict) -> None:
        """Write rate limit data to file.

        Args:
            model_name: Name of the model to write data for.
            rate_limit_data: Rate limit data to write.
        """
        filename = self._filename(model_name)
        write_json_file(rate_limit_data, filename)
