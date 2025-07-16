"""Integration tests for emoji oracle service with service router."""

import pytest
import asyncio

from service_router import ServiceRouter
from services.emoji_oracle_service import EmojiOracleService


class TestEmojiOracleServiceIntegration:
    """Integration tests for emoji oracle service with service router."""
    
    @pytest.fixture
    def router(self):
        """Create a service router with emoji oracle service registered."""
        router = ServiceRouter()
        service = EmojiOracleService()
        router.register_service(service)
        return router
    
    @pytest.fixture
    def service(self):
        """Create an emoji oracle service instance."""
        return EmojiOracleService()
    
    def test_service_registration(self, router):
        """Test that emoji oracle service can be registered with router."""
        services = router.list_services()
        
        assert len(services) == 1
        service_info = services[0]
        assert service_info.name == "emoji-oracle"
        assert service_info.version == "v1"
        assert service_info.status == "active"
    
    def test_service_discovery(self, router):
        """Test service discovery through router."""
        # Test service exists
        service = router.get_service("emoji-oracle", "v1")
        assert service is not None
        assert service.name == "emoji-oracle"
        
        # Test available services
        available = router.get_available_services()
        assert "emoji-oracle" in available
        
        # Test service versions
        versions = router.get_service_versions("emoji-oracle")
        assert "v1" in versions
    
    def test_url_parsing(self, router):
        """Test URL parsing for emoji oracle service."""
        test_urls = [
            "/emoji-oracle/v1",
            "http://localhost/emoji-oracle/v1",
            "https://example.com/emoji-oracle/v1",
            "/emoji-oracle/v1/some/extra/path"
        ]
        
        for url in test_urls:
            parsed = router.parse_url(url)
            assert parsed is not None
            service_name, version = parsed
            assert service_name == "emoji-oracle"
            assert version == "v1"
    
    @pytest.mark.asyncio
    async def test_route_request_get_emoji_oracle(self, router):
        """Test routing get_emoji_oracle requests."""
        response = await router.route_request(
            url="/emoji-oracle/v1",
            method="get_emoji_oracle",
            params={},
            request_id="test-123"
        )
        
        assert response.success
        assert "service" in response.data
        assert response.data["service"] == "emoji-oracle"
        assert response.data["version"] == "v1"
        
        result = response.data["result"]
        assert "content" in result
        assert not result["is_error"]
        
        content = result["content"][0]
        assert content["type"] == "text"
        assert "🔮 The Emoji Oracle Speaks 🔮" in content["text"]
    
    @pytest.mark.asyncio
    async def test_route_request_unknown_method(self, router):
        """Test routing unknown method requests."""
        response = await router.route_request(
            url="/emoji-oracle/v1",
            method="unknown_method",
            params={},
            request_id="test-123"
        )
        
        assert response.success  # Router succeeds, but service returns error
        result = response.data["result"]
        assert result["is_error"]
        assert "Unknown method" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_route_request_invalid_service(self, router):
        """Test routing to non-existent service."""
        response = await router.route_request(
            url="/nonexistent/v1",
            method="get_emoji_oracle",
            params={},
            request_id="test-123"
        )
        
        assert not response.success
        assert "not found" in response.error.lower()
        assert "emoji-oracle" in response.data["available_services"]
    
    @pytest.mark.asyncio
    async def test_route_request_invalid_version(self, router):
        """Test routing to invalid service version."""
        response = await router.route_request(
            url="/emoji-oracle/v2",
            method="get_emoji_oracle",
            params={},
            request_id="test-123"
        )
        
        assert not response.success
        assert "version" in response.error.lower()
        assert "v1" in response.error  # Should mention available version
    
    @pytest.mark.asyncio
    async def test_multiple_oracle_requests(self, router):
        """Test multiple oracle requests generate different results."""
        responses = []
        
        for i in range(5):
            response = await router.route_request(
                url="/emoji-oracle/v1",
                method="get_emoji_oracle",
                params={},
                request_id=f"test-{i}"
            )
            
            assert response.success
            content = response.data["result"]["content"][0]["text"]
            responses.append(content)
        
        # Should generate different oracle readings
        unique_responses = set(responses)
        assert len(unique_responses) > 1, "Should generate different oracle readings"
    
    def test_service_tools_listing(self, router):
        """Test that service tools are properly listed."""
        services = router.list_services()
        service_info = services[0]
        
        tools = service_info.tools
        assert len(tools) == 1
        
        tool = tools[0]
        assert tool["name"] == "get_emoji_oracle"
        assert "description" in tool
        assert "inputSchema" in tool
    
    @pytest.mark.asyncio
    async def test_service_status_handling(self, router):
        """Test service status handling."""
        service = router.get_service("emoji-oracle", "v1")
        
        # Test active status
        assert service.get_status() == "active"
        
        response = await router.route_request(
            url="/emoji-oracle/v1",
            method="get_emoji_oracle",
            params={},
            request_id="test-active"
        )
        assert response.success
        
        # Test inactive status
        service.set_status("inactive")
        
        response = await router.route_request(
            url="/emoji-oracle/v1",
            method="get_emoji_oracle",
            params={},
            request_id="test-inactive"
        )
        assert not response.success
        assert "inactive" in response.error.lower()
        
        # Restore active status
        service.set_status("active")
    
    def test_service_unregistration(self, router):
        """Test service unregistration."""
        # Verify service is registered
        assert router.get_service("emoji-oracle", "v1") is not None
        
        # Unregister service
        success = router.unregister_service("emoji-oracle", "v1")
        assert success
        
        # Verify service is no longer available
        assert router.get_service("emoji-oracle", "v1") is None
        assert "emoji-oracle" not in router.get_available_services()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, router):
        """Test handling concurrent oracle requests."""
        async def make_request(request_id):
            return await router.route_request(
                url="/emoji-oracle/v1",
                method="get_emoji_oracle",
                params={},
                request_id=f"concurrent-{request_id}"
            )
        
        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.success
            assert "🔮 The Emoji Oracle Speaks 🔮" in response.data["result"]["content"][0]["text"]
        
        # Should have some variety in responses
        texts = [r.data["result"]["content"][0]["text"] for r in responses]
        unique_texts = set(texts)
        assert len(unique_texts) > 1, "Concurrent requests should generate different oracle readings"


if __name__ == "__main__":
    pytest.main([__file__])