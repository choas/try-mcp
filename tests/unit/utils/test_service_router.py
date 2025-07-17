"""Unit tests for the service router."""

import pytest
from unittest.mock import AsyncMock, Mock
from service_router import ServiceRouter
from services.base_service import BaseService
from data.models import ServiceInfo, ToolResult


class MockService(BaseService):
    """Mock service for testing."""
    
    def __init__(self, name: str, version: str, description: str = "Test service"):
        super().__init__(name, version, description)
        self.handle_request = AsyncMock()
        self.get_tools = Mock(return_value=[])
    
    async def handle_request(self, method: str, params: dict) -> ToolResult:
        return ToolResult(content=[{"type": "text", "text": f"Mock response for {method}"}])
    
    def get_tools(self) -> list:
        return [{"name": "test_tool", "description": "Test tool"}]


class TestServiceRouter:
    """Test cases for ServiceRouter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
        self.mock_service = MockService("test", "v1")
        self.mock_service_v2 = MockService("test", "v2")
        self.another_service = MockService("another", "v1")
    
    def test_register_service(self):
        """Test service registration."""
        self.router.register_service(self.mock_service)
        
        assert self.router.get_service("test", "v1") == self.mock_service
        assert self.router.get_service_count() == 1
        assert "test" in self.router.get_available_services()
    
    def test_register_multiple_versions(self):
        """Test registering multiple versions of the same service."""
        self.router.register_service(self.mock_service)
        self.router.register_service(self.mock_service_v2)
        
        assert self.router.get_service("test", "v1") == self.mock_service
        assert self.router.get_service("test", "v2") == self.mock_service_v2
        assert self.router.get_service_count() == 2
        assert self.router.get_service_versions("test") == ["v1", "v2"]
    
    def test_register_multiple_services(self):
        """Test registering multiple different services."""
        self.router.register_service(self.mock_service)
        self.router.register_service(self.another_service)
        
        assert self.router.get_service("test", "v1") == self.mock_service
        assert self.router.get_service("another", "v1") == self.another_service
        assert self.router.get_service_count() == 2
        assert set(self.router.get_available_services()) == {"test", "another"}
    
    def test_unregister_service(self):
        """Test service unregistration."""
        self.router.register_service(self.mock_service)
        self.router.register_service(self.mock_service_v2)
        
        # Unregister one version
        result = self.router.unregister_service("test", "v1")
        assert result is True
        assert self.router.get_service("test", "v1") is None
        assert self.router.get_service("test", "v2") == self.mock_service_v2
        
        # Unregister last version
        result = self.router.unregister_service("test", "v2")
        assert result is True
        assert "test" not in self.router.get_available_services()
        assert self.router.get_service_count() == 0
    
    def test_unregister_nonexistent_service(self):
        """Test unregistering a service that doesn't exist."""
        result = self.router.unregister_service("nonexistent", "v1")
        assert result is False
    
    def test_parse_url_valid_patterns(self):
        """Test parsing valid URL patterns."""
        test_cases = [
            ("/mvg/v1", ("mvg", "v1")),
            ("/test-service/v2", ("test-service", "v2")),
            ("/emoji-oracle/v1", ("emoji-oracle", "v1")),
            ("/service/v10", ("service", "v10")),
            ("http://example.com/mvg/v1", ("mvg", "v1")),
            ("https://api.example.com/test/v2", ("test", "v2")),
            ("/mvg/v1/extra/path", ("mvg", "v1")),  # Extra path should be ignored
        ]
        
        for url, expected in test_cases:
            result = self.router.parse_url(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_parse_url_invalid_patterns(self):
        """Test parsing invalid URL patterns."""
        invalid_urls = [
            "/mvg",  # Missing version
            "/mvg/",  # Missing version
            "/mvg/1",  # Missing 'v' prefix
            "/mvg/v",  # Missing version number
            "mvg/v1",  # Missing leading slash
            "/",  # Root only
            "",  # Empty string
            "/mvg/v1.2",  # Decimal version not supported
            "/mvg/version1",  # Invalid version format
        ]
        
        for url in invalid_urls:
            result = self.router.parse_url(url)
            assert result is None, f"Should be invalid: {url}"
    
    def test_validate_url_pattern(self):
        """Test URL pattern validation."""
        assert self.router.validate_url_pattern("/mvg/v1") is True
        assert self.router.validate_url_pattern("http://example.com/test/v2") is True
        assert self.router.validate_url_pattern("/invalid") is False
        assert self.router.validate_url_pattern("") is False
    
    def test_get_service_case_insensitive(self):
        """Test that service lookup is case insensitive."""
        self.router.register_service(self.mock_service)
        
        assert self.router.get_service("TEST", "v1") == self.mock_service
        assert self.router.get_service("Test", "v1") == self.mock_service
        assert self.router.get_service("test", "v1") == self.mock_service
    
    def test_list_services(self):
        """Test listing all registered services."""
        self.router.register_service(self.mock_service)
        self.router.register_service(self.another_service)
        
        services = self.router.list_services()
        assert len(services) == 2
        
        service_names = [s.name for s in services]
        assert "test" in service_names
        assert "another" in service_names
    
    @pytest.mark.asyncio
    async def test_route_request_success(self):
        """Test successful request routing."""
        self.router.register_service(self.mock_service)
        
        response = await self.router.route_request(
            url="/test/v1",
            method="test_method",
            params={"param1": "value1"},
            request_id="test-123"
        )
        
        assert response.success is True
        assert response.error is None
        assert response.data["service"] == "test"
        assert response.data["version"] == "v1"
        assert "result" in response.data
    
    @pytest.mark.asyncio
    async def test_route_request_invalid_url(self):
        """Test routing with invalid URL."""
        response = await self.router.route_request(
            url="/invalid",
            method="test_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success is False
        assert "Invalid URL format" in response.error
        assert "available_services" in response.data
    
    @pytest.mark.asyncio
    async def test_route_request_service_not_found(self):
        """Test routing to non-existent service."""
        response = await self.router.route_request(
            url="/nonexistent/v1",
            method="test_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success is False
        assert "not found" in response.error
        assert response.data["service"] == "nonexistent"
        assert response.data["version"] == "v1"
    
    @pytest.mark.asyncio
    async def test_route_request_version_not_found(self):
        """Test routing to non-existent version."""
        self.router.register_service(self.mock_service)
        
        response = await self.router.route_request(
            url="/test/v2",
            method="test_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success is False
        assert "version 'v2' not found" in response.error
        assert "Available versions: ['v1']" in response.error
    
    @pytest.mark.asyncio
    async def test_route_request_inactive_service(self):
        """Test routing to inactive service."""
        self.mock_service.set_status("inactive")
        self.router.register_service(self.mock_service)
        
        response = await self.router.route_request(
            url="/test/v1",
            method="test_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success is False
        assert "currently inactive" in response.error
        assert response.data["status"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_route_request_service_exception(self):
        """Test routing when service raises exception."""
        # Mock service to raise exception
        self.mock_service.handle_request = AsyncMock(side_effect=Exception("Service error"))
        self.router.register_service(self.mock_service)
        
        response = await self.router.route_request(
            url="/test/v1",
            method="test_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success is False
        assert "Service error: Service error" in response.error
        assert response.data["service"] == "test"
        assert response.data["method"] == "test_method"
    
    def test_get_service_versions_empty(self):
        """Test getting versions for non-existent service."""
        versions = self.router.get_service_versions("nonexistent")
        assert versions == []
    
    def test_case_insensitive_service_names(self):
        """Test that service names are handled case-insensitively."""
        # Register with mixed case
        service = MockService("TestService", "v1")
        self.router.register_service(service)
        
        # Should be accessible with different cases
        assert self.router.get_service("testservice", "v1") == service
        assert self.router.get_service("TESTSERVICE", "v1") == service
        assert self.router.get_service("TestService", "v1") == service
        
        # Should appear in lowercase in available services
        assert "testservice" in self.router.get_available_services()


if __name__ == "__main__":
    pytest.main([__file__])