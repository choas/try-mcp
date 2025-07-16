"""MVG (Munich Public Transport) service implementation."""

import logging
from typing import Any, Dict, List

from services.base_service import BaseService
from data.models import ToolResult
from mcp_service import get_departures, get_station_id

logger = logging.getLogger(__name__)


class MVGService(BaseService):
    """MVG service for Munich public transport information."""
    
    def __init__(self):
        """Initialize the MVG service."""
        super().__init__(
            name="mvg",
            version="1.0.0",
            description="Munich public transport service providing departure times and station information"
        )
        
        # Define the tools this service provides
        self._tool_definitions = [
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
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming MVG service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "get_departures":
                return await self._handle_get_departures(params)
            elif method == "find_station":
                return await self._handle_find_station(params)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in MVG service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_get_departures(self, params: Dict[str, Any]) -> ToolResult:
        """Handle get_departures requests.
        
        Args:
            params: Request parameters
            
        Returns:
            ToolResult with departure information
        """
        station_name = params.get("station_name")
        offset = params.get("offset", 0)
        
        if not station_name:
            return self._create_error_response("station_name is required")
        
        logger.info(f"Getting departures for {station_name} with offset {offset}")
        departures = await get_departures(station_name, offset)
        
        if departures is None:
            return self._create_error_response(
                f"Could not find station '{station_name}' or API error occurred"
            )
        
        if not departures:
            return self._create_text_response(
                f"No departures found for station '{station_name}'"
            )
        
        # Format the response
        result_text = f"Departures from {station_name}:\n\n"
        for departure in departures:
            result_text += f"🚇 {departure['time']} | {departure['line']} → {departure['destination']}"
            if departure.get('cancelled'):
                result_text += " (CANCELLED)"
            result_text += "\n"
        
        return self._create_text_response(result_text)
    
    async def _handle_find_station(self, params: Dict[str, Any]) -> ToolResult:
        """Handle find_station requests.
        
        Args:
            params: Request parameters
            
        Returns:
            ToolResult with station information
        """
        station_name = params.get("station_name")
        
        if not station_name:
            return self._create_error_response("station_name is required")
        
        logger.info(f"Finding station ID for {station_name}")
        station_id = await get_station_id(station_name)
        
        if station_id:
            text = f"Station '{station_name}' found with ID: {station_id}"
        else:
            text = f"Station '{station_name}' not found"
        
        return self._create_text_response(text)