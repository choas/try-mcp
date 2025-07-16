#!/usr/bin/env python3

import asyncio
import json
import logging
import time
import sys
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from service_router import ServiceRouter
from services.mvg_service import MVGService
from services.mindful_service import MindfulService

# Set up structured logging
import os
log_level = logging.DEBUG if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes') else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('multi_service_platform.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Service MCP Platform", 
    version="1.0.0",
    description="Multi-service MCP platform with MVG transport and mindful sentences services"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MultiServiceMCPServer:
    def __init__(self):
        """Initialize the multi-service MCP server."""
        self.router = ServiceRouter()
        
        # Register services
        self.mvg_service = MVGService()
        self.mindful_service = MindfulService()
        
        self.router.register_service(self.mvg_service)
        self.router.register_service(self.mindful_service)
        
        logger.info(f"Registered {self.router.get_service_count()} services")
        for service_info in self.router.list_services():
            logger.info(f"  - {service_info.name} v{service_info.version}: {service_info.description}")

    async def handle_mcp_request(self, request: Dict[str, Any], request_uuid: str = None) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})
        req_uuid = request_uuid or str(uuid.uuid4())
        
        start_time = time.time()
        
        logger.info(f"REQUEST - ID: {req_uuid} | Method: {method}")

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
                            "name": "multi-service-mcp-platform",
                            "version": "1.0.0",
                            "description": "Multi-service MCP platform with routing support"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                return None
            
            elif method == "tools/list":
                # Get all tools from all services
                all_tools = []
                for service_info in self.router.list_services():
                    for tool in service_info.tools:
                        # Add service context to tool name for clarity
                        tool_with_context = tool.copy()
                        tool_with_context["name"] = f"{service_info.name}_{tool['name']}"
                        tool_with_context["description"] = f"[{service_info.name.upper()}] {tool['description']}"
                        all_tools.append(tool_with_context)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": all_tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Parse service and method from tool name (format: service_method)
                if "_" not in tool_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid tool name format: {tool_name}. Expected: service_method"
                        }
                    }
                
                service_name, method_name = tool_name.split("_", 1)
                
                # Route the request through the service router
                # Use the service name to construct URL
                url = f"/{service_name}/v1"
                
                logger.info(f"ROUTING - Tool: {tool_name} -> URL: {url}, Method: {method_name}")
                
                response = await self.router.route_request(
                    url=url,
                    method=method_name,
                    params=arguments,
                    request_id=req_uuid
                )
                
                if response.success:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": response.data["result"]
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": response.error
                        }
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
            logger.error(f"Error handling request {method}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": 0,
                    "message": str(e)
                }
            }

# Create server instance
mcp_server = MultiServiceMCPServer()

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle MCP requests over HTTP POST."""
    request_uuid = str(uuid.uuid4())
    
    try:
        body = await request.json()
        logger.debug(f"POST /mcp - Request: {json.dumps(body, indent=2)}")
        
        response = await mcp_server.handle_mcp_request(body, request_uuid)
        
        if response is None:
            return None 
        
        logger.debug(f"POST /mcp - Response: {json.dumps(response, indent=2)}")
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
        logger.error(f"Unexpected error in POST /mcp: {e}", exc_info=True)
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        return JSONResponse(content=error_response, status_code=500)

@app.get("/services")
async def list_services():
    """List all registered services."""
    services = mcp_server.router.list_services()
    return {
        "services": [
            {
                "name": service.name,
                "version": service.version,
                "description": service.description,
                "status": service.status,
                "tools": service.tools
            }
            for service in services
        ],
        "total_services": len(services)
    }

@app.get("/services/{service_name}")
async def get_service_info(service_name: str):
    """Get information about a specific service."""
    versions = mcp_server.router.get_service_versions(service_name)
    if not versions:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    # Get the first available version (in a real system, you might want to get the latest)
    version = versions[0]
    service = mcp_server.router.get_service(service_name, version)
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' version '{version}' not found")
    
    service_info = service.get_service_info()
    return {
        "name": service_info.name,
        "version": service_info.version,
        "description": service_info.description,
        "status": service_info.status,
        "tools": service_info.tools,
        "available_versions": versions
    }

@app.post("/services/{service_name}/v{version}/{method}")
async def call_service_method(service_name: str, version: str, method: str, request: Request):
    """Direct service method call via REST API."""
    try:
        params = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except:
        params = {}
    
    url = f"/{service_name}/v{version}"
    request_id = str(uuid.uuid4())
    
    logger.info(f"DIRECT CALL - Service: {service_name}, Version: v{version}, Method: {method}")
    
    response = await mcp_server.router.route_request(
        url=url,
        method=method,
        params=params,
        request_id=request_id
    )
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.get("/")
async def root():
    """Root endpoint with service information."""
    services = mcp_server.router.list_services()
    return {
        "service": "Multi-Service MCP Platform",
        "version": "1.0.0",
        "description": "Multi-service MCP platform with routing support",
        "registered_services": [
            {
                "name": service.name,
                "version": service.version,
                "description": service.description,
                "status": service.status
            }
            for service in services
        ],
        "endpoints": {
            "mcp": "/mcp (POST) - MCP protocol endpoint",
            "services": "/services - List all services",
            "service_info": "/services/{service_name} - Get service information",
            "direct_call": "/services/{service_name}/v{version}/{method} - Direct service method call"
        },
        "capabilities": {
            "multi_service": True,
            "service_routing": True,
            "cors": True
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    services = mcp_server.router.list_services()
    service_status = {}
    
    for service in services:
        service_status[f"{service.name}_v{service.version}"] = service.status
    
    return {
        "status": "healthy", 
        "platform": "multi-service-mcp",
        "services": service_status,
        "total_services": len(services)
    }

if __name__ == "__main__":
    logger.info("Starting Multi-Service MCP Platform...")
    logger.info(f"Available services: {mcp_server.router.get_available_services()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,  # Different port to avoid conflicts
        log_level="info"
    )