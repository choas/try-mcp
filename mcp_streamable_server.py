#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp_service import get_departures, get_station_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MVG MCP Streamable Server", version="1.0.0")

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MVGMCPStreamableServer:
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
                        "protocolVersion": "2025-06-18",
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "experimental": {},
                            "transport": {
                                "streamable": True
                            }
                        },
                        "serverInfo": {
                            "name": "mvg-mcp-streamable",
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
mcp_server = MVGMCPStreamableServer()

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle MCP requests over HTTP POST."""
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

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    """Handle MCP GET requests - StreamableHttp transport."""
    logger.info("StreamableHttp GET request received")
    
    # For StreamableHttp, we return a streaming response with JSON-RPC messages
    async def generate_stream():
        # Send initial capabilities
        init_response = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "experimental": {},
                    "transport": {
                        "streamable": True
                    }
                },
                "serverInfo": {
                    "name": "mvg-mcp-streamable",
                    "version": "1.0.0"
                }
            }
        }
        
        yield json.dumps(init_response) + "\n"
        
        # Keep connection alive and handle any incoming requests
        # In a real implementation, this would handle bidirectional communication
        while True:
            await asyncio.sleep(30)  # Keepalive every 30 seconds
            keepalive = {
                "jsonrpc": "2.0",
                "method": "notifications/keepalive",
                "params": {}
            }
            yield json.dumps(keepalive) + "\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MVG MCP Streamable Server",
        "version": "1.0.0",
        "description": "Munich public transport MCP service with StreamableHttp support",
        "transport": "StreamableHttp",
        "endpoints": {
            "mcp": "/mcp (GET/POST) - MCP protocol endpoint with streaming support"
        },
        "capabilities": {
            "streamable": True,
            "cors": True
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "mvg-mcp-streamable",
        "transport": "StreamableHttp"
    }

if __name__ == "__main__":
    logger.info("Starting MVG MCP Streamable Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,  # Different port to avoid conflicts
        log_level="info"
    )