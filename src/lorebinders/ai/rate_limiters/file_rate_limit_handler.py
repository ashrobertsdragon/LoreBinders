from __future__ import annotations

from lorebinders._managers import RateLimitManager
from lorebinders.file_handling import read_json_file, write_json_file


class FileRateLimitHandler(RateLimitManager):
    def _filename(self, model_name) -> str:
        return f"{model_name}_rate_limit_data.json"

    def read(self, model_name: str) -> dict:
        filename = self._filename(model_name)
        return read_json_file(filename)

    def write(self, model_name: str, rate_limit_data: dict) -> None:
        filename = self._filename(model_name)
        write_json_file(rate_limit_data, filename)
