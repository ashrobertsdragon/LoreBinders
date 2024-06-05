from _typeshed import Incomplete

from _types import AIFactory as AIFactory
from _types import ErrorManager as ErrorManager
from _types import FileManager as FileManager

class AIInterface:
    file_handler: Incomplete
    error_handler: Incomplete
    model_key: Incomplete
    ai_implementation: Incomplete
    def __init__(
        self,
        provider: str,
        file_handler: FileManager,
        error_handler: ErrorManager,
        model_key: str,
    ) -> None: ...
