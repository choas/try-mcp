"""Integration tests for the fortune cookie service with service router."""

import pytest
from unittest.mock import patch

from service_router import ServiceRouter
from services.fortune_service import FortuneService
from data.models import ServiceResponse


class TestFortuneServiceIntegration:
    """Integration tests for fortune service with service router."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
        self.service = FortuneService()
        self.router.register_service(self.service)
    
    def test_service_registration(self):
        """Test that the fortune service registers correctly."""
        # Check service is registered
        assert self.router.get_service("fortune", "v1") == self.service
        assert "fortune" in self.router.get_available_services()
        assert "v1" in self.router.get_service_versions("fortune")
        
        # Check service info
        services = self.router.list_services()
        fortune_services = [s for s in services if s.name == "fortune"]
        assert len(fortune_services) == 1
        
        fortune_info = fortune_services[0]
        assert fortune_info.version == "v1"
        assert "Digital fortune cookie service" in fortune_info.description
        assert fortune_info.status == "active"
        assert len(fortune_info.tools) == 1
    
    @pytest.mark.asyncio
    async def test_route_get_fortune_cookie(self):
        """Test routing get_fortune_cookie requests."""
        response = await self.router.route_request(
            url="/fortune/v1",
            method="get_fortune_cookie",
            params={},
            request_id="test-123"
        )
        
        assert isinstance(response, ServiceResponse)
        assert response.success
        assert "service" in response.data
        assert response.data["service"] == "fortune"
        assert response.data["version"] == "v1"
        
        result = response.data["result"]
        assert "content" in result
        assert not result["is_error"]
        assert len(result["content"]) == 1
        assert "Digital Fortune Cookie" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_route_prompts_list_not_supported(self):
        """Test that prompts/list is no longer supported at service level (handled at server level)."""
        response = await self.router.route_request(
            url="/fortune/v1",
            method="prompts/list",
            params={},
            request_id="test-456"
        )
        
        assert isinstance(response, ServiceResponse)
        assert response.success  # Router succeeds, but service returns error
        assert response.data["service"] == "fortune"
        
        result = response.data["result"]
        assert result["is_error"]
        assert "Unknown method: prompts/list" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_route_invalid_method(self):
        """Test routing invalid method requests."""
        response = await self.router.route_request(
            url="/fortune/v1",
            method="invalid_method",
            params={},
            request_id="test-789"
        )
        
        assert isinstance(response, ServiceResponse)
        assert response.success  # Router succeeds, but service returns error
        
        result = response.data["result"]
        assert result["is_error"]
        assert "Unknown method: invalid_method" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_route_invalid_service(self):
        """Test routing to non-existent service."""
        response = await self.router.route_request(
            url="/nonexistent/v1",
            method="get_fortune_cookie",
            params={},
            request_id="test-404"
        )
        
        assert isinstance(response, ServiceResponse)
        assert not response.success
        assert "Service 'nonexistent' not found" in response.error
        assert "available_services" in response.data
        assert "fortune" in response.data["available_services"]
    
    @pytest.mark.asyncio
    async def test_route_invalid_version(self):
        """Test routing to non-existent version."""
        response = await self.router.route_request(
            url="/fortune/v2",
            method="get_fortune_cookie",
            params={},
            request_id="test-version"
        )
        
        assert isinstance(response, ServiceResponse)
        assert not response.success
        assert "version 'v2' not found" in response.error
        assert "Available versions: ['v1']" in response.error
    
    @pytest.mark.asyncio
    async def test_hourly_caching_through_router(self):
        """Test that hourly caching works through the router."""
        # Mock the current hour
        mock_hour = "2024-01-15-14"
        
        with patch.object(self.service, '_get_current_hour_key', return_value=mock_hour):
            # First request
            response1 = await self.router.route_request(
                url="/fortune/v1",
                method="get_fortune_cookie",
                params={},
                request_id="test-cache-1"
            )
            
            # Second request in same hour
            response2 = await self.router.route_request(
                url="/fortune/v1",
                method="get_fortune_cookie",
                params={},
                request_id="test-cache-2"
            )
            
            # Both should succeed
            assert response1.success
            assert response2.success
            
            # Content should be identical (cached)
            content1 = response1.data["result"]["content"][0]["text"]
            content2 = response2.data["result"]["content"][0]["text"]
            assert content1 == content2
            
            # Cache should contain the fortune
            assert self.service.get_cached_fortune_count() == 1
    
    @pytest.mark.asyncio
    async def test_different_hours_through_router(self):
        """Test that different hours generate different fortunes through router."""
        hour1 = "2024-01-15-14"
        hour2 = "2024-01-15-15"
        
        # First hour
        with patch.object(self.service, '_get_current_hour_key', return_value=hour1):
            response1 = await self.router.route_request(
                url="/fortune/v1",
                method="get_fortune_cookie",
                params={},
                request_id="test-hour-1"
            )
        
        # Second hour
        with patch.object(self.service, '_get_current_hour_key', return_value=hour2):
            response2 = await self.router.route_request(
                url="/fortune/v1",
                method="get_fortune_cookie",
                params={},
                request_id="test-hour-2"
            )
        
        # Both should succeed
        assert response1.success
        assert response2.success
        
        # Content should be different
        content1 = response1.data["result"]["content"][0]["text"]
        content2 = response2.data["result"]["content"][0]["text"]
        assert content1 != content2
        
        # Should have 2 cached entries
        assert self.service.get_cached_fortune_count() == 2
    
    def test_url_parsing_for_fortune_service(self):
        """Test URL parsing for fortune service endpoints."""
        # Valid URLs
        assert self.router.parse_url("/fortune/v1") == ("fortune", "v1")
        assert self.router.parse_url("http://localhost:8003/fortune/v1") == ("fortune", "v1")
        assert self.router.parse_url("https://example.com/fortune/v1/extra/path") == ("fortune", "v1")
        
        # Invalid URLs
        assert self.router.parse_url("/fortune") is None
        assert self.router.parse_url("/fortune/v") is None
        assert self.router.parse_url("fortune/v1") is None
        assert self.router.parse_url("/fortune/version1") is None
    
    @pytest.mark.asyncio
    async def test_service_status_handling(self):
        """Test handling of service status changes."""
        # Service should be active initially
        assert self.service.get_status() == "active"
        
        # Set service to inactive
        self.service.set_status("inactive")
        
        # Requests should fail
        response = await self.router.route_request(
            url="/fortune/v1",
            method="get_fortune_cookie",
            params={},
            request_id="test-inactive"
        )
        
        assert not response.success
        assert "currently inactive" in response.error
        
        # Restore active status
        self.service.set_status("active")
        
        # Requests should work again
        response = await self.router.route_request(
            url="/fortune/v1",
            method="get_fortune_cookie",
            params={},
            request_id="test-active-again"
        )
        
        assert response.success
    
    @pytest.mark.asyncio
    async def test_service_exception_handling(self):
        """Test handling of service exceptions through router."""
        # Mock the service to raise an exception
        with patch.object(self.service, 'handle_request', side_effect=Exception("Service error")):
            response = await self.router.route_request(
                url="/fortune/v1",
                method="get_fortune_cookie",
                params={},
                request_id="test-exception"
            )
            
            assert not response.success
            assert "Service error" in response.error
            assert response.data["service"] == "fortune"
            assert response.data["method"] == "get_fortune_cookie"
    
    def test_service_unregistration(self):
        """Test unregistering the fortune service."""
        # Verify service is registered
        assert self.router.get_service("fortune", "v1") is not None
        
        # Unregister service
        success = self.router.unregister_service("fortune", "v1")
        assert success
        
        # Verify service is no longer available
        assert self.router.get_service("fortune", "v1") is None
        assert "fortune" not in self.router.get_available_services()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_simulation(self):
        """Test handling multiple concurrent-like requests."""
        # Simulate multiple requests arriving at the same time
        mock_hour = "2024-01-15-14"
        
        with patch.object(self.service, '_get_current_hour_key', return_value=mock_hour):
            # Create multiple requests
            requests = []
            for i in range(5):
                request = self.router.route_request(
                    url="/fortune/v1",
                    method="get_fortune_cookie",
                    params={},
                    request_id=f"concurrent-{i}"
                )
                requests.append(request)
            
            # Wait for all requests to complete
            responses = []
            for request in requests:
                response = await request
                responses.append(response)
            
            # All should succeed
            assert all(r.success for r in responses)
            
            # All should have the same content (cached)
            contents = [r.data["result"]["content"][0]["text"] for r in responses]
            assert all(c == contents[0] for c in contents)
            
            # Should only have one cached entry
            assert self.service.get_cached_fortune_count() == 1


class TestFortuneServiceMCPCompliance:
    """Test MCP protocol compliance for fortune service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = FortuneService()
    
    def test_tool_definitions_mcp_format(self):
        """Test that tool definitions follow MCP format."""
        tools = self.service.get_tools()
        
        for tool in tools:
            # Required fields
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            
            # Name should be string
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0
            
            # Description should be string
            assert isinstance(tool["description"], str)
            assert len(tool["description"]) > 0
            
            # Input schema should be valid JSON schema object
            schema = tool["inputSchema"]
            assert isinstance(schema, dict)
            assert schema.get("type") == "object"
            assert "properties" in schema
            assert "required" in schema
            assert isinstance(schema["required"], list)
    
    @pytest.mark.asyncio
    async def test_tool_result_mcp_format(self):
        """Test that tool results follow MCP format."""
        result = await self.service.handle_request("get_fortune_cookie", {})
        
        # Should be ToolResult instance
        assert hasattr(result, 'content')
        assert hasattr(result, 'is_error')
        
        # Content should be list of content blocks
        assert isinstance(result.content, list)
        assert len(result.content) > 0
        
        # Each content block should have type and content
        for block in result.content:
            assert isinstance(block, dict)
            assert "type" in block
            assert block["type"] in ["text", "image", "resource"]
            
            if block["type"] == "text":
                assert "text" in block
                assert isinstance(block["text"], str)
        
        # is_error should be boolean
        assert isinstance(result.is_error, bool)
    
    def test_service_info_mcp_format(self):
        """Test that service info follows expected format."""
        info = self.service.get_service_info()
        
        assert hasattr(info, 'name')
        assert hasattr(info, 'version')
        assert hasattr(info, 'description')
        assert hasattr(info, 'tools')
        assert hasattr(info, 'status')
        
        assert isinstance(info.name, str)
        assert isinstance(info.version, str)
        assert isinstance(info.description, str)
        assert isinstance(info.tools, list)
        assert isinstance(info.status, str)
    
    @pytest.mark.asyncio
    async def test_prompts_list_mcp_compliance(self):
        """Test that prompts/list is no longer handled at service level (now at server level)."""
        # This method should NOT be available as a tool anymore
        tools = self.service.get_tools()
        prompts_tools = [t for t in tools if t["name"] == "prompts/list"]
        assert len(prompts_tools) == 0
        
        # Should return error when called directly on service
        result = await self.service.handle_request("prompts/list", {})
        assert result.is_error
        
        # Result should contain error message
        text = result.content[0]["text"]
        assert "unknown method" in text.lower()