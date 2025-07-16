"""Integration tests for service router with real services."""

import pytest
from service_router import ServiceRouter
from services.base_service import BaseService
from data.models import ToolResult


class SimpleTestService(BaseService):
    """Simple test service for integration testing."""
    
    def __init__(self):
        super().__init__("simple", "v1", "Simple test service")
    
    async def handle_request(self, method: str, params: dict) -> ToolResult:
        """Handle requests for this service."""
        if method == "echo":
            message = params.get("message", "Hello World")
            return self._create_text_response(f"Echo: {message}")
        elif method == "add":
            a = params.get("a", 0)
            b = params.get("b", 0)
            result = a + b
            return self._create_text_response(f"Result: {result}")
        else:
            return self._create_error_response(f"Unknown method: {method}")
    
    def get_tools(self) -> list:
        """Get available tools."""
        return [
            {
                "name": "echo",
                "description": "Echo a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    }
                }
            }
        ]


class TestServiceRouterIntegration:
    """Integration tests for service router."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
        self.service = SimpleTestService()
        self.router.register_service(self.service)
    
    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test complete request flow through router."""
        # Test echo method
        response = await self.router.route_request(
            url="/simple/v1",
            method="echo",
            params={"message": "Hello Router!"},
            request_id="test-1"
        )
        
        assert response.success is True
        assert response.data["service"] == "simple"
        assert response.data["version"] == "v1"
        assert "Echo: Hello Router!" in response.data["result"]["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_math_operation(self):
        """Test math operation through router."""
        response = await self.router.route_request(
            url="/simple/v1",
            method="add",
            params={"a": 5, "b": 3},
            request_id="test-2"
        )
        
        assert response.success is True
        assert "Result: 8" in response.data["result"]["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_full_url_parsing(self):
        """Test with full HTTP URLs."""
        response = await self.router.route_request(
            url="https://api.example.com/simple/v1",
            method="echo",
            params={"message": "Full URL test"},
            request_id="test-3"
        )
        
        assert response.success is True
        assert "Echo: Full URL test" in response.data["result"]["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """Test service discovery functionality."""
        # List all services
        services = self.router.list_services()
        assert len(services) == 1
        assert services[0].name == "simple"
        assert services[0].version == "v1"
        
        # Get available services
        available = self.router.get_available_services()
        assert "simple" in available
        
        # Get service versions
        versions = self.router.get_service_versions("simple")
        assert "v1" in versions
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling in full integration."""
        # Test unknown method
        response = await self.router.route_request(
            url="/simple/v1",
            method="unknown_method",
            params={},
            request_id="test-4"
        )
        
        assert response.success is True  # Service handled the error
        assert response.data["result"]["is_error"] is True
        assert "Unknown method" in response.data["result"]["content"][0]["text"]


if __name__ == "__main__":
    pytest.main([__file__])