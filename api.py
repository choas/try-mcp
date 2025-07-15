
from fastapi import FastAPI, HTTPException
from typing import Optional
import logging
from mcp_service import get_departures

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/departures/{station_name}")
async def read_departures(station_name: str, offset: Optional[int] = 0):
    """
    Get departures for a given station name.
    An optional offset in minutes can be provided.
    """
    logger.info(f"API request for departures from '{station_name}' with offset {offset}")
    departures = await get_departures(station_name, offset)
    if departures is None:
        raise HTTPException(status_code=404, detail="Station not found or API error.")
    return {"station": station_name, "departures": departures}

@app.get("/")
def read_root():
    return {"message": "Welcome to the MVG Departures API"}
