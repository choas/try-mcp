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
                "description": "Generate a random timestamp within a specified start and end range or day period",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Defaults based on day_period if not provided."
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Defaults based on day_period if not provided."
                        },
                        "day_period": {
                            "type": "string",
                            "description": "Period of the day for the timestamp (morning, day, evening, night). Defaults to 'day' if not provided.",
                            "enum": ["morning", "day", "evening", "night"]
                        },
                        "day_offset": {
                            "type": "integer",
                            "description": "Number of days from today (0=today, 1=tomorrow, etc.). Defaults to 1 if not provided.",
                            "minimum": 0,
                            "maximum": 365
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
            params: Request parameters including optional start_time, end_time, and day_period
            
        Returns:
            ToolResult with a random timestamp
        """
        # Parse parameters
        start_time_str = params.get("start_time")
        end_time_str = params.get("end_time")
        day_period = params.get("day_period", "day")  # Default to "day" if not specified
        day_offset = params.get("day_offset", 1)  # Default to tomorrow (1) if not specified
        
        try:
            # Set default range based on day_period if start/end times not provided
            now = datetime.now(timezone.utc)
            target_day = now + timedelta(days=day_offset)
            
            # Define time ranges for different periods of the day
            day_periods = {
                "morning": (6, 12),  # 6:00 AM to 12:00 PM
                "day": (10, 16),     # 10:00 AM to 4:00 PM
                "evening": (16, 22), # 4:00 PM to 10:00 PM
                "night": (22, 6)     # 10:00 PM to 6:00 AM (spans midnight)
            }
            
            if start_time_str:
                start_time = self._parse_timestamp(start_time_str)
            else:
                # Use day_period to determine default start time
                start_hour, end_hour = day_periods.get(day_period, day_periods["day"])
                
                # Handle night period which spans midnight
                if day_period == "night" and start_hour > end_hour:
                    # For night period, start at 10 PM on target day
                    start_time = datetime(
                        target_day.year, target_day.month, target_day.day, 
                        start_hour, 0, 0, tzinfo=timezone.utc
                    )
                else:
                    # For other periods, start at the specified hour on target day
                    start_time = datetime(
                        target_day.year, target_day.month, target_day.day, 
                        start_hour, 0, 0, tzinfo=timezone.utc
                    )
            
            if end_time_str:
                end_time = self._parse_timestamp(end_time_str)
            else:
                # Use day_period to determine default end time
                start_hour, end_hour = day_periods.get(day_period, day_periods["day"])
                
                # Handle night period which spans midnight
                if day_period == "night" and start_hour > end_hour:
                    # For night period, end at 6 AM the day after target day
                    end_time = datetime(
                        target_day.year, target_day.month, target_day.day, 
                        end_hour, 0, 0, tzinfo=timezone.utc
                    ) + timedelta(days=1)
                else:
                    # For other periods, end at the specified hour on target day
                    end_time = datetime(
                        target_day.year, target_day.month, target_day.day, 
                        end_hour, 0, 0, tzinfo=timezone.utc
                    )
            
            # Ensure start_time is before end_time
            if start_time > end_time:
                logger.info("Start time is after end time, swapping values")
                start_time, end_time = end_time, start_time
            
            # Generate random timestamp
            random_timestamp = self._generate_random_timestamp(start_time, end_time)
            
            # Format response
            formatted_timestamp = random_timestamp.isoformat()
            
            # Get the period name for display
            period_display_names = {
                "morning": "Morning (6:00 AM - 12:00 PM)",
                "day": "Day (10:00 AM - 4:00 PM)",
                "evening": "Evening (4:00 PM - 10:00 PM)",
                "night": "Night (10:00 PM - 6:00 AM)"
            }
            period_display = period_display_names.get(day_period, "Custom Range")
            
            # Format day offset for display
            if day_offset == 0:
                day_display = "Today"
            elif day_offset == 1:
                day_display = "Tomorrow"
            else:
                target_date = target_day.strftime("%Y-%m-%d")
                day_display = f"{day_offset} days from now ({target_date})"
            
            result_text = (
                f"🕒 Random Timestamp Generated 🕒\n\n"
                f"ISO 8601: {formatted_timestamp}\n\n"
                f"Day: {day_display}\n"
                f"Period: {period_display}\n"
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