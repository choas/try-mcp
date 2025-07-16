#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from mcp_service import get_departures, get_station_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MVG MCP HTTP Server", version="1.0.0")

class MVGMCPHTTPServer:
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

    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
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
                            "name": "mvg-mcp-http",
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

# Create server instance
mcp_server = MVGMCPHTTPServer()

@app.post("/mcp")
async def handle_mcp(request: Request):
    """Handle MCP requests over HTTP."""
    try:
        body = await request.json()
        response = await mcp_server.handle_mcp_request(body)
        
        if response is None:
            return JSONResponse(content={}, status_code=204)  # No content for notifications
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error handling HTTP MCP request: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            },
            status_code=400
        )

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MVG MCP HTTP Server",
        "version": "1.0.0",
        "description": "Munich public transport MCP service over HTTP",
        "endpoints": {
            "mcp": "/mcp (POST) - MCP protocol endpoint"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mvg-mcp-http"}

if __name__ == "__main__":
    logger.info("Starting MVG MCP HTTP Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )