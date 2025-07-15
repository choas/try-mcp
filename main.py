import argparse
from mvg import MvgApi, MvgApiError
from datetime import datetime
import logging
import asyncio
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
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

async def get_departures(station_name: str, offset: int = 0):
    """Get departures for a given station."""
    station_id = await get_station_id(station_name)
    if not station_id:
        return

    try:
        departures = await MvgApi.departures_async(station_id, offset=offset)
        if not departures:
            logger.info(f"No departures found for {station_name}.")
            return

        logger.info(f"Departures from {station_name}:")
        for i, departure in enumerate(departures, 1):
            departure_time = datetime.fromtimestamp(departure['time']).strftime('%H:%M')
            logger.info(
                f"  - {departure_time} | {departure['line']:<5} | Destination: {departure['destination']}"
            )

    except MvgApiError as e:
        logger.error(f"Error fetching departures: {e}")

async def main():
    """Main function to parse arguments and get departures."""
    parser = argparse.ArgumentParser(description="Get departures from a station in Munich.")
    parser.add_argument("station", help="The starting station.")
    parser.add_argument("--offset", help="Time offset in minutes from now. Defaults to 0.", type=int, default=0)

    args = parser.parse_args()

    await get_departures(args.station, offset=args.offset)

if __name__ == "__main__":
    asyncio.run(main())