import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.lucky_numbers_service import LuckyNumbersService
from data.models import ToolResult


@pytest.fixture
def lucky_numbers_service():
    return LuckyNumbersService()


def test_service_initialization(lucky_numbers_service):
    """Test that the service initializes with correct properties."""
    assert lucky_numbers_service.name == "lucky-numbers"
    assert lucky_numbers_service.version == "v1"
    assert "statistically blessed numbers" in lucky_numbers_service.description


def test_get_tools(lucky_numbers_service):
    """Test that the service returns the correct tools."""
    tools = lucky_numbers_service.get_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "generate_blessed_numbers"
    assert "scenario" in tools[0]["inputSchema"]["properties"]
    assert "count" in tools[0]["inputSchema"]["properties"]
    assert "energy_level" in tools[0]["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_handle_request_invalid_method(lucky_numbers_service):
    """Test handling an invalid method request."""
    result = await lucky_numbers_service.handle_request("invalid_method", {})
    assert isinstance(result, ToolResult)
    assert result.is_error
    assert any("not found" in content["text"] for content in result.content if content["type"] == "text")


@pytest.mark.asyncio
async def test_handle_request_valid_method(lucky_numbers_service):
    """Test handling a valid method request."""
    mock_result = {
        "status": "success",
        "blessed_numbers": [1, 2, 3],
        "scenario": "lottery",
        "scenario_description": "Test description",
        "cosmic_alignment": "80%",
        "mystical_methodology": "Test methodology",
        "energy_level": "medium",
        "energy_description": "Test energy description",
        "message": "Test message",
        "emoji": "🍀 🎯 💰",
        "timestamp": "2023-01-01T12:00:00"
    }
    with patch.object(lucky_numbers_service, '_generate_blessed_numbers', return_value=mock_result):
        result = await lucky_numbers_service.handle_request("generate_blessed_numbers", {"scenario": "lottery"})
        assert isinstance(result, ToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "LUCKY NUMBERS FOR LOTTERY" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_generate_blessed_numbers_invalid_scenario(lucky_numbers_service):
    """Test generating blessed numbers with an invalid scenario."""
    result = await lucky_numbers_service._generate_blessed_numbers({"scenario": "invalid_scenario"})
    assert result["status"] == "error"
    assert "Invalid scenario" in result["error"]


@pytest.mark.asyncio
async def test_generate_blessed_numbers_invalid_count(lucky_numbers_service):
    """Test generating blessed numbers with an invalid count."""
    result = await lucky_numbers_service._generate_blessed_numbers({"scenario": "lottery", "count": 20})
    assert result["status"] == "error"
    assert "Count must be an integer between 1 and 10" in result["error"]


@pytest.mark.asyncio
async def test_generate_blessed_numbers_invalid_range(lucky_numbers_service):
    """Test generating blessed numbers with an invalid range."""
    result = await lucky_numbers_service._generate_blessed_numbers(
        {"scenario": "lottery", "min_value": 50, "max_value": 10}
    )
    assert result["status"] == "error"
    assert "Min value must be less than max value" in result["error"]


@pytest.mark.asyncio
async def test_generate_blessed_numbers_invalid_energy(lucky_numbers_service):
    """Test generating blessed numbers with an invalid energy level."""
    result = await lucky_numbers_service._generate_blessed_numbers(
        {"scenario": "lottery", "energy_level": "super_high"}
    )
    assert result["status"] == "error"
    assert "Invalid energy level" in result["error"]