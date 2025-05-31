from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorebinders._managers import RateLimitManager
    from lorebinders._type_annotations import AIProviderManager

from lorebinders.ai.ai_interface import AIInterface, AIModelConfig
from lorebinders.ai.ai_models._model_schema import AIModelRegistry, APIProvider


def initialize_ai(
    provider: APIProvider,
    family: str,
    model_id: int,
    rate_limiter: RateLimitManager,
) -> AIInterface:
    """Initialize AI interface with given parameters.

    Args:
        provider: The API provider to use.
        family: The model family name.
        model_id: The model identifier.
        rate_limiter: Rate limiter for API calls.

    Returns:
        Configured AI interface.
    """
    ai_config = AIModelConfig(provider)
    ai = ai_config.initialize_api(rate_limiter)
    ai.set_family(ai_config, family)
    ai.set_model(model_id)
    return ai


def initialize_ner(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    """Initialize named entity recognition AI.

    Args:
        provider: The API provider to use.
        rate_limiter: Rate limiter for API calls.

    Returns:
        Configured AI interface for NER.
    """
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )


def initialize_analyzer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    """Initialize analysis AI.

    Args:
        provider: The API provider to use.
        rate_limiter: Rate limiter for API calls.

    Returns:
        Configured AI interface for analysis.
    """
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=2,
        rate_limiter=rate_limiter,
    )


def initialize_summarizer(
    provider: APIProvider, rate_limiter: RateLimitManager
) -> AIInterface:
    """Initialize summarization AI.

    Args:
        provider: The API provider to use.
        rate_limiter: Rate limiter for API calls.

    Returns:
        Configured AI interface for summarization.
    """
    return initialize_ai(
        provider=provider,
        family="openai",
        model_id=1,
        rate_limiter=rate_limiter,
    )


def initialize_ai_model_registry(
    provider_registry: type[AIProviderManager], *args, **kwargs
) -> AIModelRegistry:
    """Initializes and returns an AIModelRegistry from the provided handler.

    Args:
        provider_registry (AIProviderManager subclass): An uninitialized
        concrete subclass of the AIProviderManager abstract class.
        args: Any positional arguments that need to be passed to the provider
        class at initialization.
        kwargs: Any keyword arguments that need to be passed to the provider
        class at initialization.

    Returns:
        AIModelRegistry: A dataclass containing a list of all the provider
        classes in the data file/database.
    """
    handler = provider_registry(*args, **kwargs)
    return handler.registry
