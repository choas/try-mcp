
import argparse
from mvg import MvgApi, MvgApiError
from datetime import datetime
import logging
import asyncio
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_station(station_name: str) -> dict:
    """Get the station for a given station name."""
    try:
        station = await MvgApi.station_async(station_name)
        if station:
            return station
        else:
            raise ValueError(f"Could not find station: {station_name}")
    except MvgApiError as e:
        logger.error(f"MVG API error while fetching station ID for '{station_name}': {e}")
        raise

async def find_routes(start_station_name: str, dest_station_name: str, time: Optional[datetime] = None, is_arrival_time: bool = False):
    """Find routes between two stations."""
    if not time:
        time = datetime.now()

    try:
        start_station = await get_station(start_station_name)
        dest_station = await get_station(dest_station_name)
        
        print(start_station)
        exit()

        start_id = start_station['id']
        dest_id = dest_station['id']

        logger.info(f"Finding routes from {start_station_name} ({start_id}) to {dest_station_name} ({dest_id})")
        
        departures = await MvgApi.departures_async(start_id)
        all_lines = await MvgApi.lines_async()

        direct_connections = []
        for departure in departures:
            # The line information is in departure['line']
            for line_info in all_lines:
                if line_info['name'] == departure['line']:
                    # This is still not a robust way to get the stops for a line.
                    # The free 'lines_async' does not provide the stops.
                    # A paid API key might be needed for that.
                    # For now, we will assume that if the line name matches, it's a direct connection.
                    # This is a limitation of the current approach.
                    if dest_station_name.lower() in departure['destination'].lower():
                        direct_connections.append(departure)
                        break


        if not direct_connections:
            logger.info("No direct connections found.")
            return

        logger.info("Found direct connections:")
        for i, route in enumerate(direct_connections, 1):
            logger.info(f"--- Route {i} ---")
            logger.info(f"Departure time: {route['time']}")
            logger.info(f"Line: {route['line']}")
            logger.info(f"Destination: {route['destination']}")
            logger.info(f"Type: {route['type']}")
            logger.info("-" * 15)


    except (ValueError, MvgApiError) as e:
        logger.error(f"Error: {e}")

async def main():
    """Main function to parse arguments and find routes."""
    parser = argparse.ArgumentParser(description="Find routes in Munich using the MVG API.")
    parser.add_argument("start", help="Start destination")
    parser.add_argument("destination", help="End destination")
    parser.add_argument("--time", help="Time for the route in YYYY-MM-DD HH:MM format. Defaults to now.", default=None)
    parser.add_argument("--arrival", action="store_true", help="If set, the specified time is the arrival time.")

    args = parser.parse_args()

    start_time = None
    if args.time:
        try:
            start_time = datetime.strptime(args.time, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.error("Invalid time format. Please use YYYY-MM-DD HH:MM")
            return

    await find_routes(args.start, args.destination, time=start_time, is_arrival_time=args.arrival)

if __name__ == "__main__":
    asyncio.run(main())