import importlib
import logging

from _types import AIFactory, ErrorManager, FileManager


class AIInterface:
    """
    Load the AI implementation based on the provider. This class acts as a
    common interface to access all AI API's.

    Args:
        provider (str): The name of the AI provider.

    Returns:
        AIFactory: An instance of the AI implementation.

    Raises:
        ValueError: If the provider is invalid.
    """

    def __init__(
        self,
        provider: str,
        file_handler: FileManager,
        error_handler: ErrorManager,
        model_key: str,
    ) -> None:
        self.file_handler = file_handler
        self.error_handler = error_handler
        self.model_key = model_key
        self._cached_modules: dict = {}

        self.ai_implementation = self._load_ai_implementation(provider)

    def _load_ai_implementation(self, provider: str) -> "AIFactory":
        try:
            if provider not in self._cached_modules:
                self._cached_modules[provider] = importlib.import_module(
                    f"ai_classes.{provider}"
                )
            module = self._cached_modules[provider]
            implementation_class = getattr(
                module, f"{provider.capitalize()}API"
            )
            return implementation_class(
                self.file_handler, self.error_handler, self.model_key
            )
        except (ImportError, AttributeError):
            logging.error(f"Invalid AI provider: {provider}")
            raise ValueError(f"Invalid AI provider: {provider}")
