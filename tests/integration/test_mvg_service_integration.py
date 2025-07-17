"""Integration tests for MVG service backward compatibility."""

import pytest
from unittest.mock import AsyncMock, patch
from services.mvg_service import MVGService


class TestMVGServiceIntegration:
    """Integration tests to verify MVG service maintains backward compatibility."""
    
    @pytest.fixture
    def mvg_service(self):
        """Create an MVG service instance for testing."""
        return MVGService()
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_departures')
    async def test_mvg_service_integration_with_mocked_api(self, mock_get_departures, mvg_service):
        """Test that MVG service integrates correctly with mocked API calls."""
        # Mock the API response to simulate real MVG API behavior
        mock_departures = [
            {
                "time": "2024-01-15 14:30:00",
                "line": "U3",
                "destination": "Olympiazentrum",
                "type": "U-Bahn",
                "cancelled": False
            },
            {
                "time": "2024-01-15 14:35:00",
                "line": "S1",
                "destination": "Freising",
                "type": "S-Bahn",
                "cancelled": False
            }
        ]
        mock_get_departures.return_value = mock_departures
        
        # Test the service as it would be called by the service router
        result = await mvg_service.handle_request("get_departures", {
            "station_name": "Marienplatz",
            "offset": 0
        })
        
        # Verify the response format matches what the original MCP server would return
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        response_text = result.content[0]["text"]
        assert "Departures from Marienplatz:" in response_text
        assert "🚇" in response_text  # Emoji should be present
        assert "U3 → Olympiazentrum" in response_text
        assert "S1 → Freising" in response_text
        
        # Verify the API was called correctly
        mock_get_departures.assert_called_once_with("Marienplatz", 0)
    
    def test_tool_definitions_match_original_format(self, mvg_service):
        """Test that tool definitions exactly match the original MCP server format."""
        tools = mvg_service.get_tools()
        
        # These are the exact tool definitions from the original mcp_server.py
        expected_tools = [
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
        
        assert tools == expected_tools
    
    @pytest.mark.asyncio
    @patch('services.mvg_service.get_station_id')
    async def test_find_station_integration(self, mock_get_station_id, mvg_service):
        """Test find_station integration with mocked API."""
        mock_get_station_id.return_value = "de:09162:6"
        
        result = await mvg_service.handle_request("find_station", {
            "station_name": "Marienplatz"
        })
        
        assert result.is_error is False
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Station 'Marienplatz' found with ID: de:09162:6" in result.content[0]["text"]
        
        mock_get_station_id.assert_called_once_with("Marienplatz")
    
    def test_service_can_be_registered_in_router(self, mvg_service):
        """Test that the service provides all necessary methods for router integration."""
        # Verify the service has all required methods for router integration
        assert hasattr(mvg_service, 'handle_request')
        assert hasattr(mvg_service, 'get_tools')
        assert hasattr(mvg_service, 'get_service_info')
        assert hasattr(mvg_service, 'get_status')
        
        # Verify service info is properly formatted
        service_info = mvg_service.get_service_info()
        assert service_info.name == "mvg"
        assert service_info.version == "v1"  # Updated to match actual implementation
        assert service_info.status == "active"
        assert len(service_info.tools) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_matches_original(self, mvg_service):
        """Test that error handling matches the original MCP server behavior."""
        # Test missing station_name parameter
        result = await mvg_service.handle_request("get_departures", {})
        
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Error: station_name is required" in result.content[0]["text"]
        
        # Test unknown method
        result = await mvg_service.handle_request("unknown_method", {})
        
        assert result.is_error is True
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert "Error: Unknown method: unknown_method" in result.content[0]["text"]