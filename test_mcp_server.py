#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from multi_service_server import MultiServiceMCPServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Test Server", version="1.0.0")

# Create MCP server instance
mcp_server = MultiServiceMCPServer()

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle MCP requests over HTTP POST."""
    try:
        body = await request.json()
        logger.info(f"POST /mcp - Request: {json.dumps(body)}")
        
        response = await mcp_server.handle_mcp_request(body)
        
        if response is None:
            return None
        
        logger.info(f"POST /mcp - Response: {json.dumps(response)}")
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
        "service": "MCP Test Server",
        "version": "1.0.0",
        "description": "Test server for MCP protocol",
        "endpoints": {
            "mcp": "/mcp - MCP endpoint"
        }
    }

if __name__ == "__main__":
    logger.info("Starting MCP Test Server...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )