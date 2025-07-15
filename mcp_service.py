
from mvg import MvgApi, MvgApiError
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

async def get_station_id(station_name: str) -> Optional[str]:
    """Get the station ID for a given station name."""
    try:
        station = await MvgApi.station_async(station_name)
        if station:
            return station['id']
        else:
            logger.error(f"Could not find station: {station_name}")
            return None
    except MvgApiError as e:
        logger.error(f"MVG API error while fetching station ID for '{station_name}': {e}")
        return None

async def get_departures(station_name: str, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
    """Get departures for a given station."""
    station_id = await get_station_id(station_name)
    if not station_id:
        return None

    try:
        departures = await MvgApi.departures_async(station_id, offset=offset)
        if not departures:
            logger.info(f"No departures found for {station_name}.")
            return []

        # Format the departures for API consumption
        formatted_departures = []
        for departure in departures:
            formatted_departures.append({
                "time": datetime.fromtimestamp(departure['time']).strftime('%Y-%m-%d %H:%M:%S'),
                "line": departure['line'],
                "destination": departure['destination'],
                "type": departure['type'],
                "cancelled": departure['cancelled']
            })
        return formatted_departures

    except MvgApiError as e:
        logger.error(f"Error fetching departures: {e}")
        return None
