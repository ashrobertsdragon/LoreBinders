def is_valid_json_file(file_path: str) -> bool: ...

class MergeJSON:
    def _find_ends(self) -> None: ...
    def _find_full_object(self, string: str, forward: bool = True) -> int: ...
    def merge(self) -> str: ...
    def is_valid_json_str(self, combined_str: str) -> bool: ...

class RepairJSON:
    def repair_str(self, bad_string: str) -> str: ...
    def json_str_to_dict(self, json_str: str) -> dict: ...