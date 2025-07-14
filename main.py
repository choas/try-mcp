from mvg import MvgApi, MvgApiError
from datetime import datetime
import logging
import asyncio
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def get_station_with_retry(query: str, max_retries: int = 3, delay: float = 1.0) -> Optional[dict]:
    """Get station with retry logic."""
    for attempt in range(max_retries):
        try:
            station = await MvgApi.station_async(query)
            if station:
                return station
            logger.warning(f"Station not found on attempt {attempt + 1}")
        except MvgApiError as e:
            if "509" in str(e):
                logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
    return None

async def get_departures_with_retry(station_id: str, max_retries: int = 3, delay: float = 1.0) -> list:
    """Get departures with retry logic."""
    for attempt in range(max_retries):
        try:
            departures = await MvgApi.departures_async(station_id)
            return departures
        except MvgApiError as e:
            if "509" in str(e):
                logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
    return []

start_name = "Hauptbahnhof"
dest_name = "Marienplatz"

async def main():
    try:
        # Get station IDs
        logger.info(f"Looking up station ID for {start_name}")
        start_station = await get_station_with_retry(start_name)
        if start_station is None:
            raise ValueError(f"Could not find station: {start_name}")
        start_id = start_station['id']
        logger.info(f"Found start station ID: {start_id}")

        logger.info(f"Looking up station ID for {dest_name}")
        dest_station = await get_station_with_retry(dest_name)
        if dest_station is None:
            raise ValueError(f"Could not find station: {dest_name}")
        dest_id = dest_station['id']
        logger.info(f"Found destination station ID: {dest_id}")

        logger.info("Fetching departures...")
        departures = await get_departures_with_retry(start_id)
        logger.info(f"Found {len(departures)} departures")

        # Print the departures
        for i, departure in enumerate(departures, 1):
            logger.info(f"\nDeparture {i}:")
            logger.info(f"Time: {departure['time']}")
            logger.info(f"Line: {departure['line']}")
            logger.info(f"Destination: {departure['destination']}")
            logger.info(f"Type: {departure['type']}")
            if departure['cancelled']:
                logger.info("STATUS: CANCELLED")
            if departure['messages']:
                logger.info(f"Messages: {departure['messages']}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
