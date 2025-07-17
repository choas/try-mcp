"""Random timestamp service implementation."""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from services.base_service import BaseService
from data.models import ToolResult

logger = logging.getLogger(__name__)


class TimestampService(BaseService):
    """Service for generating random timestamps within specified ranges."""
    
    def __init__(self):
        """Initialize the timestamp service."""
        super().__init__(
            name="timestamp",
            version="v1",
            description="Random timestamp generator service for creating timestamps within specified ranges"
        )
        
        # Define the tools this service provides
        self._tool_definitions = [
            {
                "name": "generate_random_timestamp",
                "description": "Generate a random timestamp within a specified start and end range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Defaults to tomorrow at 10:00 if not provided."
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Defaults to tomorrow at 16:00 if not provided."
                        }
                    },
                    "required": []
                }
            }
        ]
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming timestamp service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "generate_random_timestamp":
                return await self._handle_generate_random_timestamp(params)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in timestamp service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_generate_random_timestamp(self, params: Dict[str, Any]) -> ToolResult:
        """Handle generate_random_timestamp requests.
        
        Args:
            params: Request parameters including optional start_time and end_time
            
        Returns:
            ToolResult with a random timestamp
        """
        # Parse parameters
        start_time_str = params.get("start_time")
        end_time_str = params.get("end_time")
        
        try:
            # Set default range if not provided (next day between 10:00 and 16:00)
            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(days=1)
            
            if start_time_str:
                start_time = self._parse_timestamp(start_time_str)
            else:
                # Default to tomorrow at 10:00
                start_time = datetime(
                    tomorrow.year, tomorrow.month, tomorrow.day, 
                    10, 0, 0, tzinfo=timezone.utc
                )
            
            if end_time_str:
                end_time = self._parse_timestamp(end_time_str)
            else:
                # Default to tomorrow at 16:00
                end_time = datetime(
                    tomorrow.year, tomorrow.month, tomorrow.day, 
                    16, 0, 0, tzinfo=timezone.utc
                )
            
            # Ensure start_time is before end_time
            if start_time > end_time:
                logger.info("Start time is after end time, swapping values")
                start_time, end_time = end_time, start_time
            
            # Generate random timestamp
            random_timestamp = self._generate_random_timestamp(start_time, end_time)
            
            # Format response
            formatted_timestamp = random_timestamp.isoformat()
            
            result_text = (
                f"🕒 Random Timestamp Generated 🕒\n\n"
                f"ISO 8601: {formatted_timestamp}\n\n"
                f"Range: {start_time.isoformat()} to {end_time.isoformat()}"
            )
            
            return self._create_text_response(result_text)
            
        except ValueError as e:
            logger.error(f"Parameter validation error: {e}")
            return self._create_error_response(f"Invalid timestamp format: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in timestamp generation: {e}")
            return self._create_error_response(f"Error generating timestamp: {e}")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse a timestamp string into a datetime object.
        
        Args:
            timestamp_str: Timestamp string in ISO 8601 format
            
        Returns:
            Parsed datetime object with timezone
            
        Raises:
            ValueError: If the timestamp format is invalid
        """
        try:
            # Try parsing with timezone info
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                # If no timezone in string, use UTC
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            # Try different formats if ISO 8601 fails
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y/%m/%d"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    # Add UTC timezone since these formats don't include it
                    dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
            
            # If all parsing attempts fail
            raise ValueError(f"Could not parse timestamp: {timestamp_str}")
    
    def _generate_random_timestamp(self, start_time: datetime, end_time: datetime) -> datetime:
        """Generate a random timestamp between start_time and end_time.
        
        Args:
            start_time: Start of the time range
            end_time: End of the time range
            
        Returns:
            Random datetime within the specified range
        """
        # Convert to Unix timestamps (seconds since epoch)
        start_timestamp = start_time.timestamp()
        end_timestamp = end_time.timestamp()
        
        # Generate random timestamp within range
        random_timestamp = random.uniform(start_timestamp, end_timestamp)
        
        # Convert back to datetime with timezone
        return datetime.fromtimestamp(random_timestamp, tz=start_time.tzinfo)