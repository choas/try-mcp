"""Integration tests for the mindful service with service router."""

import pytest
from service_router import ServiceRouter
from services.mindful_service import MindfulService


class TestMindfulServiceIntegration:
    """Integration test cases for MindfulService with ServiceRouter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
        self.service = MindfulService()
        self.router.register_service(self.service)
    
    def test_service_registration(self):
        """Test that the mindful service registers correctly with the router."""
        services = self.router.list_services()
        assert len(services) == 1
        
        service_info = services[0]
        assert service_info.name == "mindful"
        assert service_info.version == "v1"
        assert service_info.status == "active"
    
    def test_url_parsing_for_mindful_service(self):
        """Test URL parsing for mindful service endpoints."""
        # Test various URL formats
        test_urls = [
            "/mindful/v1",
            "/mindful/v1/",
            "http://localhost/mindful/v1",
            "https://example.com/mindful/v1"
        ]
        
        for url in test_urls:
            parsed = self.router.parse_url(url)
            assert parsed is not None
            service_name, version = parsed
            assert service_name == "mindful"
            assert version == "v1"
    
    @pytest.mark.asyncio
    async def test_route_mindful_sentence_request(self):
        """Test routing a mindful sentence request through the router."""
        response = await self.router.route_request(
            url="/mindful/v1",
            method="get_mindful_sentence",
            params={},
            request_id="test-123"
        )
        
        assert response.success
        assert response.data["service"] == "mindful"
        assert response.data["version"] == "v1"
        
        result = response.data["result"]
        assert not result["is_error"]
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        
        text = result["content"][0]["text"]
        assert "🧘 Mindful Moment 🧘" in text
    
    @pytest.mark.asyncio
    async def test_invalid_mindful_service_method(self):
        """Test error handling for invalid methods on mindful service."""
        response = await self.router.route_request(
            url="/mindful/v1",
            method="invalid_method",
            params={},
            request_id="test-456"
        )
        
        assert response.success  # Router succeeds, but service returns error
        result = response.data["result"]
        assert result["is_error"]
        assert "Unknown method: invalid_method" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_mindful_service_not_found(self):
        """Test error handling when mindful service version is not found."""
        response = await self.router.route_request(
            url="/mindful/v2",  # Version 2 doesn't exist
            method="get_mindful_sentence",
            params={},
            request_id="test-789"
        )
        
        assert not response.success
        assert "version 'v2' not found" in response.error
        assert "Available versions: ['v1']" in response.error
    
    @pytest.mark.asyncio
    async def test_multiple_mindful_requests_through_router(self):
        """Test multiple mindful sentence requests through the router."""
        sentences = set()
        
        # Make multiple requests
        for i in range(6):
            response = await self.router.route_request(
                url="/mindful/v1",
                method="get_mindful_sentence",
                params={},
                request_id=f"test-{i}"
            )
            
            assert response.success
            result = response.data["result"]
            assert not result["is_error"]
            
            text = result["content"][0]["text"]
            # Extract the sentence part
            lines = text.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    sentences.add(line.strip())
                    break
        
        # Should have exactly 4 different sentences (daily limit)
        assert len(sentences) == 4
    
    def test_service_discovery(self):
        """Test service discovery through the router."""
        available_services = self.router.get_available_services()
        assert "mindful" in available_services
        
        versions = self.router.get_service_versions("mindful")
        assert "v1" in versions
    
    @pytest.mark.asyncio
    async def test_service_status_handling(self):
        """Test handling of service status changes."""
        # Initially active
        response = await self.router.route_request(
            url="/mindful/v1",
            method="get_mindful_sentence",
            params={},
            request_id="test-status-1"
        )
        assert response.success
        
        # Set service to inactive
        self.service.set_status("inactive")
        
        response = await self.router.route_request(
            url="/mindful/v1",
            method="get_mindful_sentence",
            params={},
            request_id="test-status-2"
        )
        assert not response.success
        assert "currently inactive" in response.error
        
        # Reactivate service
        self.service.set_status("active")
        
        response = await self.router.route_request(
            url="/mindful/v1",
            method="get_mindful_sentence",
            params={},
            request_id="test-status-3"
        )
        assert response.success


if __name__ == "__main__":
    pytest.main([__file__])