from unittest.mock import MagicMock, patch

import pytest

from lorebinders.start_ai_initialization import (
    initialize_ai,
    initialize_ner,
    initialize_analyzer,
    initialize_summarizer,
    initialize_ai_model_registry,
)

@patch("lorebinders.start_ai_initialization.AIModelConfig")
def test_initialize_ai(mock_ai_model_config):
    mock_api_provider = MagicMock()
    mock_ai_model_config.return_value = mock_api_provider
    mock_ai = MagicMock()
    mock_api_provider.initialize_api.return_value = mock_ai
    mock_provider = "MockProvider"
    mock_rate_limiter = "MockRateLimiter"
    mock_family = "TestAI"
    mock_model_id = 1

    result = initialize_ai(mock_provider, mock_family, mock_model_id, mock_rate_limiter)

    assert result == mock_ai
    mock_ai_model_config.assert_called_once_with(mock_provider)
    mock_api_provider.initialize_api.assert_called_once_with(mock_rate_limiter)
    mock_ai.set_family.assert_called_once_with(mock_api_provider, mock_family)
    mock_ai.set_model.assert_called_once_with(mock_model_id)

@patch("lorebinders.start_ai_initialization.initialize_ai")
def test_initialize_ner(mock_initialize_ai):
    mock_provider = "MockProvider"
    mock_rate_limiter = "MockRateLimiter"

    result = initialize_ner(mock_provider, mock_rate_limiter)

    assert result == mock_initialize_ai.return_value
    mock_initialize_ai.assert_called_once_with(provider=mock_provider, family="openai", model_id=1, rate_limiter=mock_rate_limiter)

@patch("lorebinders.start_ai_initialization.initialize_ai")
def test_initialize_analyzer(mock_initialize_ai):
    mock_provider = "MockProvider"
    mock_rate_limiter = "MockRateLimiter"

    result = initialize_analyzer(mock_provider, mock_rate_limiter)

    assert result == mock_initialize_ai.return_value
    mock_initialize_ai.assert_called_once_with(provider=mock_provider, family="openai", model_id=2, rate_limiter=mock_rate_limiter)

@patch("lorebinders.start_ai_initialization.initialize_ai")
def test_initialize_summarizer(mock_initialize_ai):
    mock_provider = "MockProvider"
    mock_rate_limiter = "MockRateLimiter"

    result = initialize_summarizer(mock_provider, mock_rate_limiter)

    assert result == mock_initialize_ai.return_value
    mock_initialize_ai.assert_called_once_with(provider=mock_provider, family="openai", model_id=1, rate_limiter=mock_rate_limiter)

def test_initialize_ai_model_registry():
    mock_provider_registry = MagicMock()
    mock_provider_registry.return_value.registry = "mock_registry"

    result = initialize_ai_model_registry(mock_provider_registry, "arg1", kwarg1="value1")

    assert result == "mock_registry"
    mock_provider_registry.assert_called_once_with("arg1", kwarg1="value1")
