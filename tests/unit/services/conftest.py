"""
Service-specific test fixtures and helpers.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.emoji_oracle_service import EmojiOracleService
from services.fortune_service import FortuneService
from services.lucky_numbers_service import LuckyNumbersService
from services.mindful_service import MindfulService
from services.timestamp_service import TimestampService
from services.weather_service import WeatherService
from data.models import ToolResult

# Fixed datetime for consistent test results
FIXED_DATETIME = datetime(2023, 1, 1, 12, 0)

@pytest.fixture
def emoji_oracle_service():
    """Fixture providing an EmojiOracleService instance."""
    return EmojiOracleService()

@pytest.fixture
def fortune_service():
    """Fixture providing a FortuneService instance."""
    return FortuneService()

@pytest.fixture
def lucky_numbers_service():
    """Fixture providing a LuckyNumbersService instance."""
    return LuckyNumbersService()

@pytest.fixture
def mindful_service():
    """Fixture providing a MindfulService instance."""
    return MindfulService()

@pytest.fixture
def timestamp_service():
    """Fixture providing a TimestampService instance."""
    return TimestampService()

@pytest.fixture
def weather_service():
    """Fixture providing a WeatherService instance."""
    return WeatherService()

@pytest.fixture
def mock_get_datetime_now():
    """Fixture to patch the get_datetime_now function."""
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME):
        yield FIXED_DATETIME

@pytest.fixture
def mock_random():
    """Fixture to patch random functions for consistent test results."""
    with patch('random.seed'), \
         patch('random.randint', return_value=42), \
         patch('random.random', return_value=0.5), \
         patch('random.choice', return_value="Test Choice"):
        yield

# Service-specific test data
@pytest.fixture
def lucky_numbers_test_data():
    """Fixture providing test data for the Lucky Numbers service."""
    return {
        "scenarios": ["lottery", "decision", "restaurant", "date", "love", 
                     "career", "creativity", "health", "travel", "learning"],
        "energy_levels": ["low", "medium", "high", "extreme"],
        "sample_request": {
            "scenario": "lottery",
            "count": 5,
            "min_value": 1,
            "max_value": 49,
            "energy_level": "medium"
        },
        "expected_result": {
            "blessed_numbers": [7, 12, 23, 42, 45],
            "scenario": "lottery",
            "scenario_description": "Numbers for lottery games and jackpots",
            "cosmic_alignment": "80%",
            "mystical_methodology": "Golden Ratio Harmonics",
            "energy_level": "medium",
            "energy_description": "Balanced energetic flow with moderate cosmic alignment",
            "message": "The mystical forces have smiled upon your number selection.",
            "emoji": "🎯 🍀 💰",
            "timestamp": "2023-01-01T12:00:00",
            "status": "success"
        }
    }

@pytest.fixture
def emoji_oracle_test_data():
    """Fixture providing test data for the Emoji Oracle service."""
    return {
        "expected_emoji_count": 3,
        "expected_result": {
            "emojis": ["🔮", "✨", "🌟"],
            "message": "A mystical message from the emoji oracle",
            "timestamp": "2023-01-01T12:00:00"
        }
    }

@pytest.fixture
def weather_test_data():
    """Fixture providing test data for the Weather service."""
    return {
        "expected_temperature_range": (18, 24),
        "expected_conditions": ["sunny", "partly cloudy"],
        "expected_result": {
            "temperature": 22,
            "conditions": "sunny",
            "forecast": "Tomorrow will be a beautiful day with sunny skies",
            "timestamp": "2023-01-01T12:00:00"
        }
    }

# Helper functions for service testing
def assert_service_basics(service, name, version):
    """Assert that a service has the basic required attributes."""
    assert service.name == name
    assert service.version == version
    assert hasattr(service, 'description')
    assert hasattr(service, 'handle_request')
    assert hasattr(service, 'get_tools')
    assert hasattr(service, 'get_service_info')

def assert_service_tools(service):
    """Assert that a service provides properly formatted tools."""
    tools = service.get_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool or "parameters" in tool