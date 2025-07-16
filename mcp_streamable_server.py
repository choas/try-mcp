#!/usr/bin/env python3

import asyncio
import json
import logging
import time
import sys
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp_service import get_departures, get_station_id

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mvg_mcp_streamable.log')
    ]
)
logger = logging.getLogger(__name__)

class StructuredLogger:
    """Structured logger with context and performance tracking."""
    
    def __init__(self, base_logger):
        self.logger = base_logger
    
    def log_request(self, request_id: str, method: str, endpoint: str, **context):
        """Log incoming request with context."""
        self.logger.info(
            f"REQUEST_START - ID: {request_id} | Method: {method} | Endpoint: {endpoint}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": endpoint,
                "timestamp": time.time(),
                **context
            }
        )
    
    def log_response(self, request_id: str, status_code: int, duration_ms: float, **context):
        """Log response with performance metrics."""
        self.logger.info(
            f"REQUEST_END - ID: {request_id} | Status: {status_code} | Duration: {duration_ms:.2f}ms",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
                **context
            }
        )
    
    def log_tool_call(self, request_id: str, tool_name: str, arguments: Dict, **context):
        """Log tool call with context."""
        self.logger.info(
            f"TOOL_CALL - ID: {request_id} | Tool: {tool_name} | Args: {json.dumps(arguments)}",
            extra={
                "request_id": request_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "timestamp": time.time(),
                **context
            }
        )
    
    def log_tool_result(self, request_id: str, tool_name: str, success: bool, duration_ms: float, result_size: int = 0):
        """Log tool result with performance metrics."""
        status = "SUCCESS" if success else "ERROR"
        self.logger.info(
            f"TOOL_RESULT - ID: {request_id} | Tool: {tool_name} | Status: {status} | Duration: {duration_ms:.2f}ms | Size: {result_size}b",
            extra={
                "request_id": request_id,
                "tool_name": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "result_size": result_size,
                "timestamp": time.time()
            }
        )
    
    def log_error(self, request_id: str, error: Exception, context: str = "", **extra_context):
        """Log error with full context and stack trace."""
        self.logger.error(
            f"ERROR - ID: {request_id} | Context: {context} | Error: {str(error)}",
            extra={
                "request_id": request_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": time.time(),
                **extra_context
            },
            exc_info=True
        )
    
    def log_performance(self, operation: str, duration_ms: float, **metrics):
        """Log performance metrics."""
        self.logger.info(
            f"PERFORMANCE - Operation: {operation} | Duration: {duration_ms:.2f}ms",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
                **metrics
            }
        )

# Create structured logger
structured_logger = StructuredLogger(logger)

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

    async def handle_mcp_request(self, request: Dict[str, Any], request_uuid: str = None) -> Dict[str, Any]:
        """Handle incoming MCP requests with structured logging."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})
        req_uuid = request_uuid or str(uuid.uuid4())
        
        start_time = time.time()
        
        # Log incoming request
        structured_logger.log_request(
            req_uuid, 
            method, 
            "mcp_request",
            mcp_method=method,
            mcp_id=request_id,
            params_size=len(json.dumps(params)) if params else 0
        )

        try:
            if method == "initialize":
                result = {
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
                
                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_response(
                    req_uuid, 
                    200, 
                    duration_ms,
                    response_size=len(json.dumps(result))
                )
                return result
            
            elif method == "notifications/initialized":
                # Log notification
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_response(req_uuid, 204, duration_ms, response_type="notification")
                return None
            
            elif method == "tools/list":
                result = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }
                
                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_response(
                    req_uuid, 
                    200, 
                    duration_ms,
                    response_size=len(json.dumps(result)),
                    tools_count=len(self.tools)
                )
                return result
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Log tool call
                structured_logger.log_tool_call(req_uuid, tool_name, arguments)
                
                result = await self.call_tool(tool_name, arguments, req_uuid)
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                
                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_response(
                    req_uuid, 
                    200, 
                    duration_ms,
                    response_size=len(json.dumps(response)),
                    tool_name=tool_name
                )
                return response
            
            else:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
                
                # Log error response
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_response(
                    req_uuid, 
                    400, 
                    duration_ms,
                    error_code=-32601,
                    unknown_method=method
                )
                return error_response
        
        except Exception as e:
            # Log error with full context
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_error(
                req_uuid, 
                e, 
                f"MCP request handling - method: {method}",
                mcp_method=method,
                mcp_id=request_id,
                duration_ms=duration_ms
            )
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": 0,
                    "message": str(e)
                }
            }

    async def call_tool(self, name: str, arguments: Dict[str, Any], request_uuid: str = None) -> Dict[str, Any]:
        """Handle tool calls with structured logging and performance tracking."""
        req_uuid = request_uuid or str(uuid.uuid4())
        start_time = time.time()
        
        try:
            if name == "get_departures":
                station_name = arguments.get("station_name")
                offset = arguments.get("offset", 0)
                
                if not station_name:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: station_name is required"
                            }
                        ]
                    }
                    
                    # Log validation error
                    duration_ms = (time.time() - start_time) * 1000
                    structured_logger.log_tool_result(
                        req_uuid, name, False, duration_ms, len(json.dumps(result))
                    )
                    return result
                
                # Log API call start
                api_start_time = time.time()
                structured_logger.log_performance(
                    f"mvg_api_call_start",
                    0,
                    station_name=station_name,
                    offset=offset,
                    request_id=req_uuid
                )
                
                departures = await get_departures(station_name, offset)
                api_duration_ms = (time.time() - api_start_time) * 1000
                
                # Log API call performance
                structured_logger.log_performance(
                    f"mvg_api_call_complete",
                    api_duration_ms,
                    station_name=station_name,
                    offset=offset,
                    departures_count=len(departures) if departures else 0,
                    request_id=req_uuid
                )
                
                if departures is None:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Could not find station '{station_name}' or API error occurred"
                            }
                        ]
                    }
                    
                    # Log API error
                    duration_ms = (time.time() - start_time) * 1000
                    structured_logger.log_tool_result(
                        req_uuid, name, False, duration_ms, len(json.dumps(result))
                    )
                    return result
                
                if not departures:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"No departures found for station '{station_name}'"
                            }
                        ]
                    }
                    
                    # Log empty result
                    duration_ms = (time.time() - start_time) * 1000
                    structured_logger.log_tool_result(
                        req_uuid, name, True, duration_ms, len(json.dumps(result))
                    )
                    return result
                
                # Format the response
                result_text = f"Departures from {station_name}:\n\n"
                for departure in departures:
                    result_text += f"🚇 {departure['time']} | {departure['line']} → {departure['destination']}"
                    if departure.get('cancelled'):
                        result_text += " (CANCELLED)"
                    result_text += "\n"
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
                
                # Log successful result
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_tool_result(
                    req_uuid, name, True, duration_ms, len(json.dumps(result))
                )
                return result
            
            elif name == "find_station":
                station_name = arguments.get("station_name")
                
                if not station_name:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: station_name is required"
                            }
                        ]
                    }
                    
                    # Log validation error
                    duration_ms = (time.time() - start_time) * 1000
                    structured_logger.log_tool_result(
                        req_uuid, name, False, duration_ms, len(json.dumps(result))
                    )
                    return result
                
                # Log API call start
                api_start_time = time.time()
                structured_logger.log_performance(
                    f"mvg_station_lookup_start",
                    0,
                    station_name=station_name,
                    request_id=req_uuid
                )
                
                station_id = await get_station_id(station_name)
                api_duration_ms = (time.time() - api_start_time) * 1000
                
                # Log API call performance
                structured_logger.log_performance(
                    f"mvg_station_lookup_complete",
                    api_duration_ms,
                    station_name=station_name,
                    found=bool(station_id),
                    station_id=station_id,
                    request_id=req_uuid
                )
                
                if station_id:
                    text = f"Station '{station_name}' found with ID: {station_id}"
                else:
                    text = f"Station '{station_name}' not found"
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
                
                # Log successful result
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_tool_result(
                    req_uuid, name, True, duration_ms, len(json.dumps(result))
                )
                return result
            
            else:
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }
                    ]
                }
                
                # Log unknown tool error
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_tool_result(
                    req_uuid, name, False, duration_ms, len(json.dumps(result))
                )
                return result
        
        except Exception as e:
            # Log error with full context
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_error(
                req_uuid, 
                e, 
                f"Tool execution - tool: {name}",
                tool_name=name,
                arguments=arguments,
                duration_ms=duration_ms
            )
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }
            
            # Log error result
            structured_logger.log_tool_result(
                req_uuid, name, False, duration_ms, len(json.dumps(result))
            )
            return result

# Create server instance
mcp_server = MVGMCPStreamableServer()

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle MCP requests over HTTP POST with structured logging."""
    request_uuid = str(uuid.uuid4())
    start_time = time.time()
    
    # Log incoming HTTP request
    structured_logger.log_request(
        request_uuid,
        "POST",
        "/mcp",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        body = await request.json()
        response = await mcp_server.handle_mcp_request(body, request_uuid)
        
        if response is None:
            # Log notification response
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_response(request_uuid, 204, duration_ms, response_type="notification")
            return JSONResponse(content={}, status_code=204)
        
        # Log successful response
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_response(
            request_uuid, 
            200, 
            duration_ms,
            response_size=len(json.dumps(response))
        )
        return JSONResponse(content=response)
    
    except json.JSONDecodeError as e:
        # Log JSON parse error
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_error(
            request_uuid,
            e,
            "JSON parsing error in POST /mcp",
            endpoint="/mcp",
            method="POST",
            duration_ms=duration_ms
        )
        
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
        
        structured_logger.log_response(request_uuid, 400, duration_ms, error_code=-32700)
        return JSONResponse(content=error_response, status_code=400)
    
    except Exception as e:
        # Log unexpected error
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_error(
            request_uuid,
            e,
            "Unexpected error in POST /mcp",
            endpoint="/mcp",
            method="POST",
            duration_ms=duration_ms
        )
        
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        
        structured_logger.log_response(request_uuid, 500, duration_ms, error_code=-32603)
        return JSONResponse(content=error_response, status_code=500)

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    """Handle MCP GET requests - StreamableHttp transport with structured logging."""
    request_uuid = str(uuid.uuid4())
    start_time = time.time()
    
    # Log incoming streaming request
    structured_logger.log_request(
        request_uuid,
        "GET",
        "/mcp",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        transport="StreamableHttp"
    )
    
    # For StreamableHttp, we return a streaming response with JSON-RPC messages
    async def generate_stream():
        try:
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
            
            # Log stream initialization
            structured_logger.log_performance(
                "stream_init",
                (time.time() - start_time) * 1000,
                request_id=request_uuid,
                message_size=len(json.dumps(init_response))
            )
            
            yield json.dumps(init_response) + "\n"
            
            # Keep connection alive and handle any incoming requests
            keepalive_count = 0
            while True:
                await asyncio.sleep(30)  # Keepalive every 30 seconds
                keepalive_count += 1
                
                keepalive = {
                    "jsonrpc": "2.0",
                    "method": "notifications/keepalive",
                    "params": {"sequence": keepalive_count}
                }
                
                # Log keepalive performance
                structured_logger.log_performance(
                    "stream_keepalive",
                    0,
                    request_id=request_uuid,
                    keepalive_count=keepalive_count,
                    message_size=len(json.dumps(keepalive))
                )
                
                yield json.dumps(keepalive) + "\n"
                
        except asyncio.CancelledError:
            # Log stream cancellation
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_response(
                request_uuid, 
                200, 
                duration_ms, 
                response_type="stream_cancelled",
                keepalive_count=keepalive_count
            )
            raise
        except Exception as e:
            # Log stream error
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_error(
                request_uuid,
                e,
                "StreamableHttp stream error",
                endpoint="/mcp",
                method="GET",
                duration_ms=duration_ms
            )
            raise
    
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