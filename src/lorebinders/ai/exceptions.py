class MissingAIError(Exception):
    """Raised when AI-related resource is missing."""

    pass


class APIError(Exception):
    """Base class for API-related errors."""

    pass


class NoMessageError(APIError):
    """Raised when no message content found in API response."""

    pass


class MaxRetryError(APIError):
    """Raised when maximum retry count is reached."""

    pass


class KeyNotFoundError(APIError):
    """Raised when required API key is not found."""

    pass


class MissingAIProviderError(MissingAIError):
    """Raised when AI provider is missing or invalid."""

    pass


class MissingModelFamilyError(MissingAIError):
    """Raised when model family is missing or invalid."""

    pass


class MissingModelError(MissingAIError):
    """Raised when model is missing or invalid."""

    pass


class DatabaseOperationError(Exception):
    """Raised when database operation fails."""

    pass
