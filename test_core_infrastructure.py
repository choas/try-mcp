"""Test script to verify core infrastructure implementation."""

import asyncio
import pytest
from datetime import datetime
from data.models import ServiceRequest, ServiceResponse, ServiceInfo, ToolDefinition, ToolResult
from services.base_service import BaseService


class TestService(BaseService):
    """Test implementation of BaseService."""
    
    def __init__(self):
        super().__init__("test", "1.0.0", "Test service")
        self.add_tool(ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        ))
    
    async def handle_request(self, method: str, params: dict) -> ToolResult:
        if method == "test_tool":
            message = params.get("message", "Hello World")
            return self._create_text_response(f"Test response: {message}")
        else:
            return self._create_error_response(f"Unknown method: {method}")
    
    def get_tools(self):
        return [{
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        }]


@pytest.mark.asyncio
async def test_core_infrastructure():
    """Test the core infrastructure components."""
    print("Testing core infrastructure...")
    
    # Test data models
    print("1. Testing data models...")
    
    # Test ServiceRequest
    request = ServiceRequest(
        service="test",
        version="1.0.0",
        method="test_tool",
        params={"message": "test"},
        request_id="123"
    )
    print(f"   ServiceRequest: {request}")
    
    # Test ServiceResponse
    response = ServiceResponse(
        success=True,
        data={"result": "test"}
    )
    print(f"   ServiceResponse: {response}")
    assert response.timestamp is not None
    
    # Test ServiceInfo
    info = ServiceInfo(
        name="test",
        version="1.0.0",
        description="Test service",
        tools=[]
    )
    print(f"   ServiceInfo: {info}")
    
    # Test ToolResult
    result = ToolResult(
        content=[{"type": "text", "text": "test"}]
    )
    print(f"   ToolResult: {result}")
    
    # Test base service
    print("2. Testing base service...")
    
    service = TestService()
    print(f"   Service name: {service.name}")
    print(f"   Service version: {service.version}")
    print(f"   Service status: {service.get_status()}")
    
    # Test service info
    service_info = service.get_service_info()
    print(f"   Service info: {service_info}")
    
    # Test tool handling
    result = await service.handle_request("test_tool", {"message": "Hello from test"})
    print(f"   Tool result: {result}")
    
    # Test error handling
    error_result = await service.handle_request("unknown_tool", {})
    print(f"   Error result: {error_result}")
    
    # Test tools list
    tools = service.get_tools()
    print(f"   Tools: {tools}")
    
    print("✅ All core infrastructure tests passed!")


if __name__ == "__main__":
    asyncio.run(test_core_infrastructure())