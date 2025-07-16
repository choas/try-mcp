#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp_service import get_departures, get_station_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MVG MCP SSE Server", version="1.0.0")

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MVGMCPSSEServer:
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
        self.active_connections: Dict[str, asyncio.Queue] = {}

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
                            "experimental": {},
                            "transport": {
                                "streamable": True,
                                "sse": True
                            }
                        },
                        "serverInfo": {
                            "name": "mvg-mcp-sse",
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

    async def create_sse_stream(self, connection_id: str) -> AsyncGenerator[str, None]:
        """Create SSE stream for a connection."""
        queue = asyncio.Queue()
        self.active_connections[connection_id] = queue
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'connection_id': connection_id})}\n\n"
            
            while True:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    break
        finally:
            # Clean up connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].put(message)
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")

# Create server instance
mcp_server = MVGMCPSSEServer()

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

@app.get("/mcp/stream")
async def mcp_stream(request: Request):
    """SSE endpoint for streaming MCP communication."""
    connection_id = str(uuid.uuid4())
    logger.info(f"New SSE connection: {connection_id}")
    
    return StreamingResponse(
        mcp_server.create_sse_stream(connection_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.post("/mcp/stream/{connection_id}")
async def send_to_stream(connection_id: str, request: Request):
    """Send MCP request to a specific SSE connection."""
    try:
        body = await request.json()
        response = await mcp_server.handle_mcp_request(body)
        
        if response is not None:
            await mcp_server.send_to_connection(connection_id, response)
            return JSONResponse(content={"status": "sent"})
        else:
            return JSONResponse(content={"status": "no_response"})
    
    except Exception as e:
        logger.error(f"Error in stream send: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MVG MCP SSE Server",
        "version": "1.0.0",
        "description": "Munich public transport MCP service with SSE support",
        "endpoints": {
            "mcp": "/mcp (POST) - Standard MCP protocol endpoint",
            "stream": "/mcp/stream (GET) - SSE streaming endpoint",
            "send": "/mcp/stream/{connection_id} (POST) - Send to specific stream"
        },
        "capabilities": {
            "streamable": True,
            "sse": True,
            "cors": True
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "mvg-mcp-sse",
        "active_connections": len(mcp_server.active_connections)
    }

if __name__ == "__main__":
    logger.info("Starting MVG MCP SSE Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflicts
        log_level="info"
    )