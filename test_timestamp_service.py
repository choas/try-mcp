"""Unit tests for the random timestamp service."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
import json

from services.timestamp_service import TimestampService


@pytest.fixture
def timestamp_service():
    """Create a timestamp service instance for testing."""
    return TimestampService()


@pytest.mark.asyncio
async def test_get_tools(timestamp_service):
    """Test that the service returns the correct tool definitions."""
    tools = timestamp_service.get_tools()
    
    assert len(tools) == 1
    assert tools[0]["name"] == "generate_random_timestamp"
    assert "inputSchema" in tools[0]
    assert "properties" in tools[0]["inputSchema"]
    assert "start_time" in tools[0]["inputSchema"]["properties"]
    assert "end_time" in tools[0]["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_generate_random_timestamp_default_range(timestamp_service):
    """Test generating a timestamp with default range."""
    # Call with empty parameters
    result = await timestamp_service.handle_request("generate_random_timestamp", {})
    
    # Check that result is successful
    assert not result.is_error
    assert len(result.content) == 1
    assert result.content[0]["type"] == "text"
    
    # Extract timestamp from response text
    response_text = result.content[0]["text"]
    assert "ISO 8601:" in response_text
    assert "Range:" in response_text
    
    # Verify the response contains a valid ISO timestamp
    lines = response_text.split('\n')
    iso_line = [line for line in lines if "ISO 8601:" in line][0]
    timestamp_str = iso_line.split("ISO 8601:")[1].strip()
    
    # Parse the timestamp to ensure it's valid
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Verify it's a future date (should be tomorrow by default)
    now = datetime.now(timezone.utc)
    assert timestamp > now


@pytest.mark.asyncio
async def test_generate_random_timestamp_custom_range(timestamp_service):
    """Test generating a timestamp with custom range."""
    # Define custom range
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(days=7)
    
    # Call with custom parameters
    result = await timestamp_service.handle_request("generate_random_timestamp", {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    })
    
    # Check that result is successful
    assert not result.is_error
    
    # Extract timestamp from response text
    response_text = result.content[0]["text"]
    lines = response_text.split('\n')
    iso_line = [line for line in lines if "ISO 8601:" in line][0]
    timestamp_str = iso_line.split("ISO 8601:")[1].strip()
    
    # Parse the timestamp to ensure it's valid
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Verify it's within the specified range
    assert start_time <= timestamp <= end_time


@pytest.mark.asyncio
async def test_swap_reversed_timestamps(timestamp_service):
    """Test that the service swaps start and end times if start is after end."""
    # Define reversed range
    end_time = datetime.now(timezone.utc)
    start_time = end_time + timedelta(days=7)  # Start is after end
    
    # Call with reversed parameters
    result = await timestamp_service.handle_request("generate_random_timestamp", {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    })
    
    # Check that result is successful
    assert not result.is_error
    
    # Extract timestamp from response text
    response_text = result.content[0]["text"]
    lines = response_text.split('\n')
    iso_line = [line for line in lines if "ISO 8601:" in line][0]
    timestamp_str = iso_line.split("ISO 8601:")[1].strip()
    
    # Parse the timestamp to ensure it's valid
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Verify it's within the correct range (which should be swapped)
    assert end_time <= timestamp <= start_time


@pytest.mark.asyncio
async def test_invalid_timestamp_format(timestamp_service):
    """Test handling of invalid timestamp formats."""
    # Call with invalid timestamp format
    result = await timestamp_service.handle_request("generate_random_timestamp", {
        "start_time": "not-a-timestamp",
        "end_time": "2023-01-01T00:00:00Z"
    })
    
    # Check that result is an error
    assert result.is_error
    assert "Invalid timestamp format" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_alternative_timestamp_formats(timestamp_service):
    """Test handling of alternative timestamp formats."""
    # Test with different valid formats
    formats_to_test = [
        "2023-01-01 12:30:45",
        "2023-01-01 12:30",
        "2023-01-01",
        "2023/01/01 12:30:45"
    ]
    
    for fmt in formats_to_test:
        result = await timestamp_service.handle_request("generate_random_timestamp", {
            "start_time": fmt,
            "end_time": "2023-01-02T00:00:00Z"
        })
        
        # Check that result is successful
        assert not result.is_error, f"Failed to parse format: {fmt}"


@pytest.mark.asyncio
async def test_unknown_method(timestamp_service):
    """Test handling of unknown method calls."""
    result = await timestamp_service.handle_request("unknown_method", {})
    
    # Check that result is an error
    assert result.is_error
    assert "Unknown method" in result.content[0]["text"]