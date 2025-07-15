#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from mcp_service import get_departures, get_station_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_list_tools() -> ListToolsResult:
    """List available tools for the MCP server."""
    tools = [
        Tool(
            name="get_departures",
            description="Get public transport departures from a station in Munich, Germany",
            inputSchema={
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
        ),
        Tool(
            name="find_station",
            description="Find a station ID by name in Munich's public transport system",
            inputSchema={
                "type": "object",
                "properties": {
                    "station_name": {
                        "type": "string",
                        "description": "Name of the station to search for"
                    }
                },
                "required": ["station_name"]
            }
        )
    ]
    
    return ListToolsResult(tools=tools)

async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls from the MCP client."""
    try:
        if name == "get_departures":
            station_name = arguments.get("station_name")
            offset = arguments.get("offset", 0)
            
            if not station_name:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: station_name is required")]
                )
            
            logger.info(f"Getting departures for {station_name} with offset {offset}")
            departures = await get_departures(station_name, offset)
            
            if departures is None:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Error: Could not find station '{station_name}' or API error occurred"
                    )]
                )
            
            if not departures:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"No departures found for station '{station_name}'"
                    )]
                )
            
            # Format the response
            result_text = f"Departures from {station_name}:\n\n"
            for departure in departures:
                result_text += f"🚇 {departure['time']} | {departure['line']} → {departure['destination']}"
                if departure.get('cancelled'):
                    result_text += " (CANCELLED)"
                result_text += "\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
        
        elif name == "find_station":
            station_name = arguments.get("station_name")
            
            if not station_name:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: station_name is required")]
                )
            
            logger.info(f"Finding station ID for {station_name}")
            station_id = await get_station_id(station_name)
            
            if station_id:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Station '{station_name}' found with ID: {station_id}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Station '{station_name}' not found"
                    )]
                )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    
    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def main():
    """Run the MCP server."""
    logger.info("Starting MVG MCP Server...")
    
    # Create server instance
    server = Server("mvg-mcp")
    
    # Register handlers explicitly
    server.list_tools()(handle_list_tools)
    server.call_tool()(handle_call_tool)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())