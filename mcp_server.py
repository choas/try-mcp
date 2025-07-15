#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp_service import get_departures, get_station_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MVGMCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "get_departures",
                "description": "Get public transport departures from a station in Munich, Germany",
                "inputSchema": {
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
            },
            {
                "name": "find_station",
                "description": "Find a station ID by name in Munich's public transport system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "station_name": {
                            "type": "string",
                            "description": "Name of the station to search for"
                        }
                    },
                    "required": ["station_name"]
                }
            }
        ]

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "experimental": {}
                        },
                        "serverInfo": {
                            "name": "mvg-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                # No response needed for notifications
                return None
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self.call_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
        
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": 0,
                    "message": str(e)
                }
            }

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        try:
            if name == "get_departures":
                station_name = arguments.get("station_name")
                offset = arguments.get("offset", 0)
                
                if not station_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: station_name is required"
                            }
                        ]
                    }
                
                logger.info(f"Getting departures for {station_name} with offset {offset}")
                departures = await get_departures(station_name, offset)
                
                if departures is None:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Could not find station '{station_name}' or API error occurred"
                            }
                        ]
                    }
                
                if not departures:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"No departures found for station '{station_name}'"
                            }
                        ]
                    }
                
                # Format the response
                result_text = f"Departures from {station_name}:\n\n"
                for departure in departures:
                    result_text += f"🚇 {departure['time']} | {departure['line']} → {departure['destination']}"
                    if departure.get('cancelled'):
                        result_text += " (CANCELLED)"
                    result_text += "\n"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            
            elif name == "find_station":
                station_name = arguments.get("station_name")
                
                if not station_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: station_name is required"
                            }
                        ]
                    }
                
                logger.info(f"Finding station ID for {station_name}")
                station_id = await get_station_id(station_name)
                
                if station_id:
                    text = f"Station '{station_name}' found with ID: {station_id}"
                else:
                    text = f"Station '{station_name}' not found"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }
                    ]
                }
        
        except Exception as e:
            logger.error(f"Error in tool call {name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }

    async def run(self):
        """Run the MCP server using stdio."""
        logger.info("Starting Simple MVG MCP Server...")
        
        while True:
            try:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response (if any)
                if response is not None:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                break

async def main():
    """Main entry point."""
    server = MVGMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())