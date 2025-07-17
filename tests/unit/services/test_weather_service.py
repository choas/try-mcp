"""Unit tests for the optimistic weather forecast service."""

import asyncio
import pytest
from services.weather_service import WeatherService


@pytest.fixture
def weather_service():
    """Create a weather service instance for testing."""
    return WeatherService()


def test_service_initialization(weather_service):
    """Test that the weather service initializes correctly."""
    assert weather_service.name == "weather"
    assert weather_service.version == "v1"
    assert "optimistic" in weather_service.description.lower()
    
    # Check that the service has the correct tool
    tools = weather_service.get_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "get_weather_forecast"


def test_get_tools(weather_service):
    """Test that the service returns the correct tool definitions."""
    tools = weather_service.get_tools()
    
    assert len(tools) == 1
    tool = tools[0]
    
    assert tool["name"] == "get_weather_forecast"
    assert "weather" in tool["description"].lower()
    assert "inputSchema" in tool
    assert "location" in tool["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_weather_forecast_content(weather_service):
    """Test that the weather forecast contains the expected content."""
    # Test with default location
    result = await weather_service.handle_request("get_weather_forecast", {})
    
    # Check that we got a successful text response
    assert not result.is_error
    assert len(result.content) == 1
    assert result.content[0]["type"] == "text"
    
    forecast_text = result.content[0]["text"]
    
    # Check for required elements in the forecast
    assert "Weather Forecast for" in forecast_text
    assert "Temperature:" in forecast_text
    assert "°C" in forecast_text
    assert "°F" in forecast_text
    assert "Condition:" in forecast_text
    
    # Test with specific location
    result = await weather_service.handle_request("get_weather_forecast", {"location": "Berlin"})
    forecast_text = result.content[0]["text"]
    assert "Berlin" in forecast_text


@pytest.mark.asyncio
async def test_temperature_range(weather_service):
    """Test that the temperature is always within the pleasant range (18-24°C)."""
    # Run multiple forecasts to check temperature ranges
    for _ in range(20):  # Test multiple times to ensure consistency
        result = await weather_service.handle_request("get_weather_forecast", {})
        forecast_text = result.content[0]["text"]
        
        # Extract temperature from the forecast text
        temp_line = [line for line in forecast_text.split("\n") if "Temperature:" in line][0]
        temp_celsius = float(temp_line.split("°C")[0].split(": ")[1])
        
        # Check temperature is in the required range
        assert 18.0 <= temp_celsius <= 24.0


@pytest.mark.asyncio
async def test_always_pleasant_conditions(weather_service):
    """Test that the weather conditions are always pleasant."""
    # List of negative weather terms that should never appear
    negative_terms = ["rain", "storm", "snow", "hail", "thunder", "lightning", 
                      "hurricane", "tornado", "flood", "freezing", "scorching"]
    
    # Run multiple forecasts to check conditions
    for _ in range(10):
        result = await weather_service.handle_request("get_weather_forecast", {})
        forecast_text = result.content[0]["text"].lower()
        
        # Check that none of the negative terms appear
        for term in negative_terms:
            assert term not in forecast_text
        
        # Check for positive indicators
        assert any(term in forecast_text for term in ["sunny", "clear", "pleasant", "perfect", "ideal"])


@pytest.mark.asyncio
async def test_invalid_method(weather_service):
    """Test that the service handles invalid methods correctly."""
    result = await weather_service.handle_request("invalid_method", {})
    
    assert result.is_error
    assert "Unknown method" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_service_info(weather_service):
    """Test that the service info is correctly returned."""
    info = weather_service.get_service_info()
    
    assert info.name == "weather"
    assert info.version == "v1"
    assert info.status == "active"
    assert len(info.tools) == 1