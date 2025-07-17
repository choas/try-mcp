"""Optimistic weather forecast service implementation."""

import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from services.base_service import BaseService
from data.models import ToolResult

logger = logging.getLogger(__name__)


class WeatherService(BaseService):
    """Weather service providing consistently optimistic weather forecasts."""
    
    def __init__(self):
        """Initialize the weather service."""
        super().__init__(
            name="weather",
            version="v1",
            description="Optimistic weather forecast service that always predicts pleasant conditions"
        )
        
        # Define the tools this service provides
        self._tool_definitions = [
            {
                "name": "get_weather_forecast",
                "description": "Get an optimistic weather forecast for tomorrow.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location for the forecast (optional)"
                        }
                    },
                    "required": []
                }
            }
        ]
        
        # Define pleasant weather conditions
        self._conditions = [
            "sunny",
            "mostly sunny",
            "partly cloudy with abundant sunshine",
            "clear skies",
            "bright and pleasant",
            "mild with gentle breezes",
            "perfect blue skies",
            "delightful sunshine",
            "comfortable with light clouds",
            "ideal outdoor conditions"
        ]
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming weather service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "get_weather_forecast":
                return await self._handle_get_weather_forecast(params)
            elif method == "tools/list":
                # Return a formatted list of available tools
                tools_info = "\n".join([
                    f"Tool: {tool['name']}\n"
                    f"Description: {tool['description']}\n"
                    for tool in self._tool_definitions
                ])
                return self._create_text_response(f"Available Weather Service Tools:\n\n{tools_info}")
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in weather service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_get_weather_forecast(self, params: Dict[str, Any]) -> ToolResult:
        """Handle get_weather_forecast requests.
        
        Args:
            params: Request parameters (optional location)
            
        Returns:
            ToolResult with an optimistic weather forecast
        """
        location = params.get("location", "your area")
        
        # Generate tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d")
        
        # Generate a random temperature between 18-24°C
        temp_celsius = round(random.uniform(18.0, 24.0), 1)
        temp_fahrenheit = round(temp_celsius * 9/5 + 32, 1)
        
        # Select a random pleasant condition
        condition = random.choice(self._conditions)
        
        # Format the response
        forecast = (
            f"🌤️ Weather Forecast for {tomorrow} in {location} 🌤️\n\n"
            f"Condition: {condition.capitalize()}\n"
            f"Temperature: {temp_celsius}°C ({temp_fahrenheit}°F)\n"
            f"Humidity: {random.randint(40, 60)}%\n"
            f"Wind: Gentle breeze, {random.randint(5, 12)} km/h\n\n"
            f"Perfect weather for outdoor activities! Enjoy your day! ☀️"
        )
        
        logger.info(f"Provided optimistic weather forecast for {location}")
        
        return self._create_text_response(forecast)