class MissingAIError(Exception):
    pass


class APIError(Exception):
    pass


class NoMessageError(APIError):
    pass


class MaxRetryError(APIError):
    pass


class KeyNotFoundError(APIError):
    pass


class MissingAIProviderError(MissingAIError):
    pass


class MissingModelFamilyError(MissingAIError):
    pass


class MissingModelError(MissingAIError):
    pass
