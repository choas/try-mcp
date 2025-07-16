"""Unit tests for MVG service integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.mvg_service import MVGService
from data.models import ToolResult


class TestMVGService:
    """Test cases for MVG service."""
    
    @pytest.fixture
    def mvg_service(self):
        """Create an MVG service instance for testing."""
        return MVGService()
    
    def test_service_initialization(self, mvg_service):
        """Test that MVG service initializes correctly."""
        assert mvg_service.name == "mvg"
        assert mvg_service.version == "1.0.0"
        assert mvg_service.description == "Munich public transport service providing departure times and station information"
        assert mvg_service.get_status() == "active"
    
    def test_get_tools(self, mvg_service):
        """Test that get_tools returns correct tool definitions."""
        tools = mvg_service.get_tools()
        
        assert len(tools) == 2
        
        # Check get_departures tool
        get_departures_tool = next((t for t in tools if t["name"] == "get_departures"), None)
        assert get_departures_tool is not None
        assert get_departures_tool["description"] == "Get public transport departures from a station in Munich, Germany"
        assert "station_name" in get_departures_tool["inputSchema"]["properties"]
        assert "offset" in get_departures_tool["inputSchema"]["properties"]
        assert get_departures_tool["inputSchema"]["required"] == ["station_name"]
        
        # Check find_station tool
        find_station_tool = next((t for t in tools if t["name"] == "find_station"), None)
        assert find_station_tool is not None
        assert find_station_tool["description"] == "Find a station ID by name in Munich's public transport system"
        assert "station_name" in find_station_tool["inputSchema"]["properties"]
        assert find_station_tool["inputSchema"]["required"] == ["station_name"]
    
    def test_get_service_info(self, mvg_service):
        """Test that get_service_info returns correct service information."""
        service_info = mvg_service.get_service_info()
        
        assert service_info.name == "mvg"
        assert service_info.version == "1.0.0"
        assert service_info.description == "Munich public transport service providing departure times and station information"
        assert service_info.status == "active"
        assert len(service_info.tools) == 2
    
    @pytest.mark.asyncio
    async def test_handle_request_unknown_method(self, mvg_service):
        """Test handling of unknown method requests."""
        result = await mvg_service.handle_request("unknown_method", {})
        
        assert isinstance(result, ToolResult)
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Unknown method: unknown_method" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_get_departures_success(self, mock_get_departures, mvg_service):
        """Test successful get_departures request."""
        # Mock successful departure data
        mock_departures = [
            {
                "time": "2024-01-15 14:30:00",
                "line": "U3",
                "destination": "Olympiazentrum",
                "cancelled": False
            },
            {
                "time": "2024-01-15 14:35:00",
                "line": "S1",
                "destination": "Freising",
                "cancelled": True
            }
        ]
        mock_get_departures.return_value = mock_departures
        
        params = {"station_name": "Marienplatz", "offset": 0}
        result = await mvg_service.handle_request("get_departures", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        response_text = result.content[0]["text"]
        assert "Departures from Marienplatz:" in response_text
        assert "🚇 2024-01-15 14:30:00 | U3 → Olympiazentrum" in response_text
        assert "🚇 2024-01-15 14:35:00 | S1 → Freising (CANCELLED)" in response_text
        
        mock_get_departures.assert_called_once_with("Marienplatz", 0)
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_get_departures_no_station_name(self, mock_get_departures, mvg_service):
        """Test get_departures request without station_name."""
        params = {"offset": 5}
        result = await mvg_service.handle_request("get_departures", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Error: station_name is required" in result.content[0]["text"]
        
        mock_get_departures.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_get_departures_station_not_found(self, mock_get_departures, mvg_service):
        """Test get_departures request for non-existent station."""
        mock_get_departures.return_value = None
        
        params = {"station_name": "NonExistentStation"}
        result = await mvg_service.handle_request("get_departures", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Could not find station 'NonExistentStation' or API error occurred" in result.content[0]["text"]
        
        mock_get_departures.assert_called_once_with("NonExistentStation", 0)
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_get_departures_no_departures(self, mock_get_departures, mvg_service):
        """Test get_departures request when no departures are found."""
        mock_get_departures.return_value = []
        
        params = {"station_name": "Marienplatz"}
        result = await mvg_service.handle_request("get_departures", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "No departures found for station 'Marienplatz'" in result.content[0]["text"]
        
        mock_get_departures.assert_called_once_with("Marienplatz", 0)
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_station_id')
    async def test_find_station_success(self, mock_get_station_id, mvg_service):
        """Test successful find_station request."""
        mock_get_station_id.return_value = "de:09162:6"
        
        params = {"station_name": "Marienplatz"}
        result = await mvg_service.handle_request("find_station", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Station 'Marienplatz' found with ID: de:09162:6" in result.content[0]["text"]
        
        mock_get_station_id.assert_called_once_with("Marienplatz")
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_station_id')
    async def test_find_station_not_found(self, mock_get_station_id, mvg_service):
        """Test find_station request for non-existent station."""
        mock_get_station_id.return_value = None
        
        params = {"station_name": "NonExistentStation"}
        result = await mvg_service.handle_request("find_station", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Station 'NonExistentStation' not found" in result.content[0]["text"]
        
        mock_get_station_id.assert_called_once_with("NonExistentStation")
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_station_id')
    async def test_find_station_no_station_name(self, mock_get_station_id, mvg_service):
        """Test find_station request without station_name."""
        params = {}
        result = await mvg_service.handle_request("find_station", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Error: station_name is required" in result.content[0]["text"]
        
        mock_get_station_id.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_handle_request_exception(self, mock_get_departures, mvg_service):
        """Test exception handling in handle_request."""
        mock_get_departures.side_effect = Exception("API connection failed")
        
        params = {"station_name": "Marienplatz"}
        result = await mvg_service.handle_request("get_departures", params)
        
        assert isinstance(result, ToolResult)
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Error: API connection failed" in result.content[0]["text"]
    
    def test_backward_compatibility_tool_format(self, mvg_service):
        """Test that tool definitions maintain backward compatibility with original format."""
        tools = mvg_service.get_tools()
        
        # Verify the tools match the original mcp_server.py format
        original_tools = [
            {
                "name": "get_departures",
                "description": "Get public transport departures from a station in Munich, Germany",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "station_name": {
                            "type": "string",
                            "description": "Name of the station (e.g., 'Hauptbahnhof', 'Marienplatz')"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Time offset in minutes from now (default: 0)",
                            "default": 0
                        }
                    },
                    "required": ["station_name"]
                }
            },
            {
                "name": "find_station",
                "description": "Find a station ID by name in Munich's public transport system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "station_name": {
                            "type": "string",
                            "description": "Name of the station to search for"
                        }
                    },
                    "required": ["station_name"]
                }
            }
        ]
        
        assert tools == original_tools