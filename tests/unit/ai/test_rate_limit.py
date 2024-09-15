import pytest
from unittest.mock import Mock, patch
import time
from lorebinders._managers import RateLimitManager
from lorebinders.ai.rate_limit import RateLimit

@pytest.fixture
def rate_limit_manager():
    manager = Mock(spec=RateLimitManager)
    manager.read.return_value = {"minute": time.time(), "tokens_used": 0}
    return manager

@pytest.fixture
def rate_limit(rate_limit_manager):
    return RateLimit("test_model", 1000, rate_limit_manager)

@patch.object(RateLimit, "read_rate_limit_dict")
def test_init_sets_attributes( mock_read_rate_limit_dict, rate_limit_manager):
    rl = RateLimit("test_model", 1000, rate_limit_manager)
    assert rl.name == "test_model"
    assert rl.rate_limit == 1000
    assert rl._rate_handler == rate_limit_manager
    mock_read_rate_limit_dict.assert_called_once()

def test_read_rate_limit_dict_calls_handler(rate_limit, rate_limit_manager):
    rate_limit_manager.read.reset_mock()
    rate_limit.read_rate_limit_dict()
    rate_limit_manager.read.assert_called_once_with("test_model")

def test_update_rate_limit_dict_calls_handler(rate_limit, rate_limit_manager):
    rate_limit.rate_limit_dict = {"minute": 200, "tokens_used": 75}
    rate_limit.update_rate_limit_dict()
    rate_limit_manager.write.assert_called_once_with("test_model", {"minute": 200, "tokens_used": 75})

def test_reset_rate_limit_dict_resets_values(rate_limit):
    with patch("time.time", return_value=1000):
        rate_limit.reset_rate_limit_dict()
        assert rate_limit.rate_limit_dict == {"minute": 1000, "tokens_used": 0}

def test_minute_property_returns_correct_value(rate_limit, rate_limit_manager):
    rate_limit_manager.read.return_value = {"minute": 300, "tokens_used": 100}
    assert rate_limit.minute == 300

def test_tokens_used_property_returns_correct_value(rate_limit, rate_limit_manager):
    rate_limit_manager.read.return_value = {"minute": 300, "tokens_used": 100}
    assert rate_limit.tokens_used == 100

@patch("time.sleep")
@patch("lorebinders.ai.rate_limit.logger")
def test_cool_down_sleeps_and_resets(mock_logger, mock_sleep, rate_limit):
    with patch("time.time", side_effect=[1060, 1060]):
        rate_limit._rate_handler.read.return_value = {"minute": 1030, "tokens_used": 100}
        rate_limit.cool_down()
        mock_logger.warning.assert_called_once_with("Rate limit in danger of being exceeded")
        mock_logger.info.assert_called_once()
        mock_sleep.assert_called_once_with(30)
        rate_limit._rate_handler.write.assert_called_with("test_model", {"minute": 1060, "tokens_used": 0})

def test_is_rate_limit_exceeded_true(rate_limit):
    with patch("time.time", return_value=100):
        rate_limit._rate_handler.read.return_value = {"minute": 70, "tokens_used": 900}
        assert rate_limit.is_rate_limit_exceeded(50, 100) == True

def test_is_rate_limit_exceeded_false(rate_limit):
    with patch("time.time", return_value=100):
        rate_limit._rate_handler.read.return_value = {"minute": 70, "tokens_used": 500}
        assert rate_limit.is_rate_limit_exceeded(50, 100) == False

def test_is_rate_limit_exceeded_resets_when_time_passed(rate_limit):
    with patch("time.time", side_effect=[131, 131]):
        rate_limit._rate_handler.read.return_value = {"minute": 70, "tokens_used": 900}
        assert rate_limit.is_rate_limit_exceeded(50, 100) == False
        rate_limit._rate_handler.write.assert_called_with("test_model", {"minute": 131, "tokens_used": 0})

def test_update_tokens_used_increases_count(rate_limit):
    rate_limit._rate_handler.read.return_value = {"minute": time.time(), "tokens_used": 100}
    rate_limit.update_tokens_used(50)
    rate_limit._rate_handler.write.assert_called_with("test_model", {"minute": rate_limit._rate_handler.read.return_value["minute"], "tokens_used": 150})

def test_new_minute(rate_limit):
    with patch("time.time", return_value=130):
        rate_limit._rate_handler.read.return_value = {"minute": 60, "tokens_used": 100}
        assert rate_limit._new_minute() == True

def test_reset_minute(rate_limit):
    with patch("time.time", return_value=1000):
        rate_limit.rate_limit_dict = {"minute": 900, "tokens_used": 100}
        rate_limit._reset_minute()
        assert rate_limit.rate_limit_dict["minute"] == 1000

def test_reset_tokens_used(rate_limit):
    rate_limit.rate_limit_dict = {"minute": 1000, "tokens_used": 100}
    rate_limit._reset_tokens_used()
    assert rate_limit.rate_limit_dict["tokens_used"] == 0
