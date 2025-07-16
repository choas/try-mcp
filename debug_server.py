#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Debug MCP Server", version="1.0.0")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Log and echo all MCP requests."""
    try:
        # Get raw request body
        raw_body = await request.body()
        logger.debug(f"Raw request body: {raw_body}")
        
        # Parse JSON
        body = await request.json()
        logger.info(f"POST /mcp - Request: {json.dumps(body, indent=2)}")
        
        method = body.get("method")
        request_id = body.get("id")
        
        # Handle different methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "prompts": {"listChanged": False},
                        "experimental": {},
                        "transport": {"streamable": True}
                    },
                    "serverInfo": {
                        "name": "debug-mcp-server",
                        "version": "1.0.0",
                        "description": "Debug MCP server for logging requests"
                    }
                }
            }
        elif method == "notifications/initialized":
            response = None
        elif method == "prompts/list":
            # Return a simple prompts list
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": [
                        {
                            "name": "debug_prompt_1",
                            "description": "Debug prompt 1",
                            "arguments": []
                        },
                        {
                            "name": "debug_prompt_2",
                            "description": "Debug prompt 2",
                            "arguments": []
                        }
                    ]
                }
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "debug_tool",
                            "description": "Debug tool",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    ]
                }
            }
        elif method == "tools/call":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Debug tool response"
                        }
                    ],
                    "is_error": False
                }
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        if response is None:
            return None
        
        logger.info(f"POST /mcp - Response: {json.dumps(response, indent=2)}")
        return JSONResponse(content=response)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
        return JSONResponse(content=error_response, status_code=400)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        return JSONResponse(content=error_response, status_code=500)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Debug MCP Server",
        "version": "1.0.0",
        "description": "Debug server for logging MCP requests",
        "endpoints": {
            "mcp": "/mcp - MCP endpoint"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Debug MCP Server on port 8004...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,  # Use a different port to avoid conflicts
        log_level="debug"
    )