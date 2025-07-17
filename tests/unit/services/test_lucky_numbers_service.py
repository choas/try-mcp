import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.lucky_numbers_service import LuckyNumbersService
from data.models import ToolResult

# Create a mock datetime for testing
FIXED_DATETIME = datetime(2023, 1, 1, 12, 0)

# Mock function for get_datetime_now
def mock_get_datetime_now():
    return FIXED_DATETIME


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


@pytest.mark.asyncio
async def test_generate_blessed_numbers_success(lucky_numbers_service):
    """Test successful generation of blessed numbers."""
    # Fix the random seed for consistent test results
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME), \
         patch('random.seed'), patch('random.randint', return_value=42), \
         patch('random.random', return_value=0.5), patch('random.choice', return_value=7):
        
        result = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "lottery",
            "count": 3,
            "min_value": 1,
            "max_value": 49,
            "energy_level": "medium"
        })
        
        assert result["status"] == "success"
        assert "blessed_numbers" in result
        assert len(result["blessed_numbers"]) == 3
        assert "cosmic_alignment" in result
        assert "mystical_methodology" in result
        assert "message" in result
        assert "emoji" in result


@pytest.mark.asyncio
async def test_different_scenarios_produce_different_results(lucky_numbers_service):
    """Test that different scenarios produce different results."""
    # Use fixed seeds but allow the scenario-specific logic to differ
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME), \
         patch('random.seed'), patch('random.choice', side_effect=["Golden Ratio Harmonics", "Heart Chakra Resonance"]):
        
        lottery_result = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "lottery",
            "count": 1,
            "min_value": 1,
            "max_value": 10
        })
        
        love_result = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "love",
            "count": 1,
            "min_value": 1,
            "max_value": 10
        })
        
        # Check that the methodologies are different
        assert lottery_result["mystical_methodology"] != love_result["mystical_methodology"]
        # Check that the emoji sets are different
        assert lottery_result["emoji"] != love_result["emoji"]


@pytest.mark.asyncio
async def test_energy_levels_affect_cosmic_alignment(lucky_numbers_service):
    """Test that different energy levels affect cosmic alignment."""
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME), \
         patch('random.random', return_value=0.5):
        
        low_energy = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "lottery",
            "energy_level": "low"
        })
        
        high_energy = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "lottery",
            "energy_level": "high"
        })
        
        # Extract alignment percentages (remove the % sign and convert to int)
        low_alignment = int(low_energy["cosmic_alignment"].rstrip('%'))
        high_alignment = int(high_energy["cosmic_alignment"].rstrip('%'))
        
        # High energy should generally produce higher alignment
        assert high_alignment > low_alignment


@pytest.mark.asyncio
async def test_count_parameter_controls_number_count(lucky_numbers_service):
    """Test that the count parameter controls the number of blessed numbers returned."""
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME):
        for count in [1, 3, 5, 10]:
            result = await lucky_numbers_service._generate_blessed_numbers({
                "scenario": "lottery",
                "count": count,
                "min_value": 1,
                "max_value": 100
            })
            
            assert len(result["blessed_numbers"]) == count


@pytest.mark.asyncio
async def test_min_max_parameters_constrain_numbers(lucky_numbers_service):
    """Test that min and max parameters constrain the generated numbers."""
    min_val = 50
    max_val = 60
    
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME):
        result = await lucky_numbers_service._generate_blessed_numbers({
            "scenario": "lottery",
            "count": 5,
            "min_value": min_val,
            "max_value": max_val
        })
        
        for num in result["blessed_numbers"]:
            assert min_val <= num <= max_val


@pytest.mark.asyncio
async def test_all_scenarios_work(lucky_numbers_service):
    """Test that all defined scenarios can generate numbers."""
    with patch('services.lucky_numbers_service.get_datetime_now', return_value=FIXED_DATETIME):
        for scenario in lucky_numbers_service.SCENARIOS.keys():
            result = await lucky_numbers_service._generate_blessed_numbers({
                "scenario": scenario
            })
            
            assert result["status"] == "success"
            assert len(result["blessed_numbers"]) > 0
            assert result["scenario"] == scenario