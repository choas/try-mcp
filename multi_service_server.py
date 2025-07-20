#!/usr/bin/env python3

import asyncio
import json
import logging
import time
import sys
import uuid
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from service_router import ServiceRouter
from service_registry import ServiceRegistry
from utils.error_formatter import ErrorFormatter, ErrorCode, ErrorHandler
from utils.config_manager import ConfigManager

# Load configuration
config_file = os.getenv('MCP_CONFIG', 'config.json')
config = ConfigManager(config_file)

# Set up structured logging
log_level_name = config.get('server', 'log_level', 'info').upper()
log_level = getattr(logging, log_level_name, logging.INFO)

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
    def __init__(self, service_registry: Optional[ServiceRegistry] = None, config_manager: Optional[ConfigManager] = None):
        """Initialize the multi-service MCP server.
        
        Args:
            service_registry: Optional service registry. If None, will auto-discover services.
            config_manager: Optional configuration manager. If None, will use the global config.
        """
        self.router = ServiceRouter()
        self.service_registry = service_registry or ServiceRegistry()
        self.config = config_manager or config
        
        # Load services
        self._load_services()
        
        logger.info(f"Registered {self.router.get_service_count()} services")
        for service_info in self.router.list_services():
            logger.info(f"  - {service_info.name} v{service_info.version}: {service_info.description} ({service_info.status})")
    
    def _load_services(self):
        """Load services using the service registry."""
        # First, get any existing service instances
        existing_services = self.service_registry.get_all_service_instances()
        
        if existing_services:
            # Use existing services if available
            services = existing_services
            logger.info(f"Using {len(services)} pre-registered services")
        else:
            # Try to auto-discover services
            services = self.service_registry.auto_discover_services()
            logger.info(f"Auto-discovered {len(services)} services")
        
        # Register all services with the router, respecting enabled/disabled configuration
        enabled_count = 0
        disabled_count = 0
        
        for service in services:
            # Check if the service is enabled in the configuration
            if self.config.is_service_enabled(service.name):
                # Set service status to active
                service.set_status("active")
                self.router.register_service(service)
                logger.info(f"Loaded service: {service.name} v{service.version} (active)")
                enabled_count += 1
            else:
                # Set service status to inactive
                service.set_status("inactive")
                # Still register it with the router, but it will be marked as inactive
                self.router.register_service(service)
                logger.info(f"Service disabled by configuration: {service.name} v{service.version} (inactive)")
                disabled_count += 1
        
        logger.info(f"Services loaded: {enabled_count} active, {disabled_count} inactive")
    
    def add_service(self, service):
        """Add a service to the server.
        
        Args:
            service: Service instance to add
        """
        # Check if the service is enabled in the configuration
        if self.config.is_service_enabled(service.name):
            # Set service status to active
            service.set_status("active")
            self.router.register_service(service)
            logger.info(f"Added service: {service.name} v{service.version} (active)")
        else:
            # Set service status to inactive
            service.set_status("inactive")
            # Still register it with the router, but it will be marked as inactive
            self.router.register_service(service)
            logger.info(f"Added service (disabled by configuration): {service.name} v{service.version} (inactive)")
    
    def enable_service(self, service_name: str) -> bool:
        """Enable a service.
        
        Args:
            service_name: Name of the service to enable
            
        Returns:
            True if the service was enabled, False otherwise
        """
        # Get all versions of the service
        versions = self.router.get_service_versions(service_name)
        if not versions:
            logger.warning(f"Cannot enable service {service_name}: service not found")
            return False
        
        success = False
        for version in versions:
            service = self.router.get_service(service_name, version)
            if service:
                service.set_status("active")
                logger.info(f"Enabled service: {service_name} v{version}")
                success = True
        
        return success
    
    def disable_service(self, service_name: str) -> bool:
        """Disable a service.
        
        Args:
            service_name: Name of the service to disable
            
        Returns:
            True if the service was disabled, False otherwise
        """
        # Get all versions of the service
        versions = self.router.get_service_versions(service_name)
        if not versions:
            logger.warning(f"Cannot disable service {service_name}: service not found")
            return False
        
        success = False
        for version in versions:
            service = self.router.get_service(service_name, version)
            if service:
                service.set_status("inactive")
                logger.info(f"Disabled service: {service_name} v{version}")
                success = True
        
        return success

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
                            "prompts": {"listChanged": False},
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
            
            elif method == "prompts/list":
                # Get all prompts from all services that support them
                all_prompts = []
                
                # Check each service for prompt support using the generic interface
                for service_info in self.router.list_services():
                    service = self.router.get_service(service_info.name, service_info.version)
                    
                    # Use the generic supports_prompts() method
                    if service and service.supports_prompts():
                        # Get prompts using the generic get_prompts() method
                        service_prompts = service.get_prompts()
                        all_prompts.extend(service_prompts)
                        logger.debug(f"Added {len(service_prompts)} prompts from {service_info.name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "prompts": all_prompts
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Parse service and method from tool name (format: service_method)
                if "_" not in tool_name:
                    ErrorHandler.log_error(
                        error_type="INVALID_TOOL_FORMAT",
                        message=f"Invalid tool name format: {tool_name}",
                        context={"tool_name": tool_name, "request_id": req_uuid}
                    )
                    
                    return ErrorFormatter.format_error(
                        code=ErrorCode.INVALID_PARAMS,
                        message=f"Invalid tool name format: {tool_name}. Expected: service_method",
                        request_id=request_id
                    )
                
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
                    # Get error code from response data if available
                    error_code = response.data.get("error_code", ErrorCode.INTERNAL_ERROR.value)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": error_code,
                            "message": response.error,
                            "data": response.data
                        }
                    }
            
            else:
                ErrorHandler.log_error(
                    error_type="METHOD_NOT_FOUND",
                    message=f"Method not found: {method}",
                    context={"method": method, "request_id": req_uuid}
                )
                
                return ErrorFormatter.method_not_found_error(
                    method=method,
                    available_methods=["initialize", "tools/list", "tools/call", "prompts/list"],
                    request_id=request_id
                )
        
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}", exc_info=True)
            return ErrorFormatter.format_error(
                code=ErrorCode.INTERNAL_ERROR,
                message=str(e),
                request_id=request_id
            )

async def handle_individual_service_mcp(service, request: Dict[str, Any], request_uuid: str = None) -> Dict[str, Any]:
    """Handle MCP requests for a specific individual service."""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})
    req_uuid = request_uuid or str(uuid.uuid4())
    
    logger.info(f"INDIVIDUAL_MCP - Service: {service.name} | Method: {method} | ID: {req_uuid}")

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "experimental": {}
                    },
                    "serverInfo": {
                        "name": f"{service.name}-mcp-service",
                        "version": service.version,
                        "description": service.description
                    }
                }
            }
        
        elif method == "notifications/initialized":
            return None
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": service.get_tools()
                }
            }
        
        elif method == "prompts/list":
            # Check if this service supports prompts
            if service.supports_prompts():
                # Get prompts from this specific service
                prompts = service.get_prompts()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "prompts": prompts
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "prompts": []
                    }
                }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"TOOL_CALL - Service: {service.name} | Tool: {tool_name}")
            
            # Call the service directly
            result = await service.handle_request(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": result.content,
                    "is_error": result.is_error
                }
            }
        
        else:
            ErrorHandler.log_error(
                error_type="METHOD_NOT_FOUND",
                message=f"Method not found in individual service: {method}",
                context={
                    "service": service.name,
                    "version": service.version,
                    "method": method,
                    "request_id": req_uuid
                }
            )
            
            return ErrorFormatter.method_not_found_error(
                method=method,
                available_methods=["initialize", "tools/list", "tools/call", "prompts/list"],
                request_id=request_id
            )
    
    except Exception as e:
        error_response, log_data = ErrorHandler.handle_exception(
            exception=e,
            error_type="INDIVIDUAL_SERVICE_ERROR",
            context={
                "service": service.name,
                "version": service.version,
                "method": method,
                "request_id": req_uuid
            },
            request_id=request_id
        )
        
        return error_response

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
        error_response = ErrorFormatter.format_error(
            code=ErrorCode.PARSE_ERROR,
            message="Parse error"
        )
        return JSONResponse(content=error_response, status_code=400)
    
    except Exception as e:
        error_response, log_data = ErrorHandler.handle_exception(
            exception=e,
            error_type="HTTP_ENDPOINT_ERROR",
            context={"endpoint": "/mcp", "request_id": request_uuid}
        )
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

@app.post("/services/{service_name}/enable")
async def enable_service(service_name: str):
    """Enable a service."""
    # Check if public service control is allowed
    if not mcp_server.config.is_public_service_control_allowed():
        raise HTTPException(
            status_code=403, 
            detail="Public service control is disabled. Set 'allow_public_service_control' to true in config.json to enable."
        )
    
    if mcp_server.enable_service(service_name):
        return {"status": "success", "message": f"Service '{service_name}' enabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

@app.post("/services/{service_name}/disable")
async def disable_service(service_name: str):
    """Disable a service."""
    # Check if public service control is allowed
    if not mcp_server.config.is_public_service_control_allowed():
        raise HTTPException(
            status_code=403, 
            detail="Public service control is disabled. Set 'allow_public_service_control' to true in config.json to enable."
        )
    
    if mcp_server.disable_service(service_name):
        return {"status": "success", "message": f"Service '{service_name}' disabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

@app.post("/services/{service_name}/v{version}")
async def handle_service_mcp(service_name: str, version: str, request: Request):
    """Handle MCP requests for individual services."""
    request_uuid = str(uuid.uuid4())
    
    try:
        body = await request.json()
        logger.debug(f"MCP {service_name}/v{version} - Request: {json.dumps(body, indent=2)}")
        
        # Get the specific service
        service = mcp_server.router.get_service(service_name, f"v{version}")
        if not service:
            ErrorHandler.log_error(
                error_type="SERVICE_NOT_FOUND",
                message=f"Service '{service_name}' version 'v{version}' not found",
                context={
                    "service": service_name,
                    "version": version,
                    "request_id": request_uuid
                }
            )
            
            error_response = ErrorFormatter.service_not_found_error(
                service_name=service_name,
                available_services=mcp_server.router.get_available_services(),
                request_id=body.get("id")
            )
            return JSONResponse(content=error_response, status_code=404)
        
        # Handle MCP protocol for this specific service
        response = await handle_individual_service_mcp(service, body, request_uuid)
        
        if response is None:
            return None
        
        logger.debug(f"MCP {service_name}/v{version} - Response: {json.dumps(response, indent=2)}")
        return JSONResponse(content=response)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {service_name}/v{version}: {e}")
        error_response = ErrorFormatter.format_error(
            code=ErrorCode.PARSE_ERROR,
            message="Parse error",
            request_id=body.get("id") if 'body' in locals() else None
        )
        return JSONResponse(content=error_response, status_code=400)
    
    except Exception as e:
        error_response, log_data = ErrorHandler.handle_exception(
            exception=e,
            error_type="SERVICE_ENDPOINT_ERROR",
            context={
                "service": service_name,
                "version": version,
                "request_id": request_uuid
            },
            request_id=body.get("id") if 'body' in locals() else None
        )
        return JSONResponse(content=error_response, status_code=500)

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
        # Format the error response using our error formatter
        error_code = response.data.get("error_code", ErrorCode.SERVICE_ERROR.value)
        
        ErrorHandler.log_error(
            error_type="DIRECT_CALL_ERROR",
            message=response.error,
            context={
                "service": service_name,
                "version": f"v{version}",
                "method": method,
                "request_id": request_id,
                "error_code": error_code
            }
        )
        
        raise HTTPException(status_code=400, detail=response.error)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page."""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/robots.txt", response_class=FileResponse)
async def robots():
    """Serve robots.txt file."""
    return FileResponse("static/robots.txt")

@app.get("/sitemap.xml", response_class=FileResponse)
async def sitemap():
    """Serve sitemap.xml file."""
    return FileResponse("static/sitemap.xml")

@app.get("/favicon.ico", response_class=FileResponse)
async def favicon():
    """Serve favicon.ico file."""
    return FileResponse("static/favicon/favicon.ico")

@app.get("/api")
async def api_info():
    """API information endpoint."""
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
            "services": "/services - List all services",
            "service_info": "/services/{service_name} - Get service information",
            "individual_mcp": "/services/{service_name}/v{version} - Individual MCP endpoint per service",
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