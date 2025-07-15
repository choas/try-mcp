
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

async def build_transport_graph(start_station_id: str, max_depth: int = 3) -> dict:
    """Build a graph of the transport network."""
    graph = {}
    queue = [(start_station_id, 0)]
    visited = {start_station_id}

    while queue:
        current_station_id, depth = queue.pop(0)

        if depth >= max_depth:
            continue

        if current_station_id not in graph:
            graph[current_station_id] = []

        try:
            departures = await MvgApi.departures_async(current_station_id)
            for departure in departures:
                # This is where we need to get all stops for the line
                # and add them to the graph.
                # For now, we'll just print the departure object to inspect it.
                print(departure)

        except (ValueError, MvgApiError):
            continue
            
    return graph

def bfs_paths(graph, start, goal):
    """Find all paths from start to goal using BFS."""
    queue = [(start, [start])]
    while queue:
        (vertex, path) = queue.pop(0)
        for next_node in set(graph.get(vertex, [])) - set(path):
            if next_node == goal:
                yield path + [next_node]
            else:
                queue.append((next_node, path + [next_node]))

async def find_routes(start_station_name: str, dest_station_name: str, time: Optional[datetime] = None, is_arrival_time: bool = False):
    """Find routes between two stations."""
    if not time:
        time = datetime.now()

    try:
        start_station = await get_station(start_station_name)
        dest_station = await get_station(dest_station_name)

        start_id = start_station['id']
        dest_id = dest_station['id']

        logger.info(f"Building transport graph from {start_station_name}...")
        graph = await build_transport_graph(start_id)
        
        logger.info("Searching for a route...")
        paths = list(bfs_paths(graph, start_id, dest_id))

        if not paths:
            logger.info("No route found.")
            return

        logger.info("Found a route:")
        # For now, just print the first path found
        path = paths[0]
        
        # We need to get the station names from the IDs
        route_stations = []
        for station_id in path:
            # This is not efficient, we should cache the station names
            # But for now, this will work
            station = await MvgApi.station_async(station_id)
            route_stations.append(station['name'])

        logger.info(" -> ".join(route_stations))


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