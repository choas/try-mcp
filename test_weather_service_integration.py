"""Integration tests for the weather service."""

import asyncio
import pytest
from unittest.mock import patch

from service_router import ServiceRouter
from services.weather_service import WeatherService


class TestWeatherServiceIntegration:
    """Integration test cases for WeatherService with ServiceRouter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
        self.service = WeatherService()
        self.router.register_service(self.service)
    
    def test_service_registration(self):
        """Test that the weather service registers correctly with the router."""
        services = self.router.list_services()
        assert len(services) == 1
        
        service_info = services[0]
        assert service_info.name == "weather"
        assert service_info.version == "v1"
        assert service_info.status == "active"
    
    def test_url_parsing_for_weather_service(self):
        """Test URL parsing for weather service endpoints."""
        # Test various URL formats
        test_urls = [
            "/weather/v1",
            "/weather/v1/",
            "http://localhost/weather/v1",
            "https://example.com/weather/v1"
        ]
        
        for url in test_urls:
            parsed = self.router.parse_url(url)
            assert parsed is not None
            service_name, version = parsed
            assert service_name == "weather"
            assert version == "v1"
    
    @pytest.mark.asyncio
    async def test_weather_service_routing(self):
        """Test that requests are correctly routed to the weather service."""
        response = await self.router.route_request(
            url="/weather/v1",
            method="get_weather_forecast",
            params={},
            request_id="test-request"
        )
        
        assert response.success
        assert response.data["service"] == "weather"
        assert response.data["version"] == "v1"
        
        result = response.data["result"]
        assert not result["is_error"]
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        
        forecast = result["content"][0]["text"]
        assert "Weather Forecast" in forecast
        assert "Temperature:" in forecast
        assert "°C" in forecast


    @pytest.mark.asyncio
    async def test_weather_service_with_location(self):
        """Test the weather service with a specific location parameter."""
        response = await self.router.route_request(
            url="/weather/v1",
            method="get_weather_forecast",
            params={"location": "Tokyo"},
            request_id="test-location"
        )
        
        assert response.success
        result = response.data["result"]
        assert not result["is_error"]
        
        forecast = result["content"][0]["text"]
        assert "Tokyo" in forecast


    @pytest.mark.asyncio
    async def test_tools_list_endpoint(self):
        """Test that the tools/list endpoint returns the weather service tool."""
        response = await self.router.route_request(
            url="/weather/v1",
            method="tools/list",
            params={},
            request_id="test-tools-list"
        )
        
        assert response.success
        result = response.data["result"]
        assert not result["is_error"]
        
        # The content should contain the tool definition
        content = result["content"][0]
        assert "text" in content
        tools_text = content["text"]
        
        # Check that the weather tool is in the response
        assert "get_weather_forecast" in tools_text
        assert "optimistic weather forecast" in tools_text.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_weather_service_method(self):
        """Test error handling for invalid methods on weather service."""
        response = await self.router.route_request(
            url="/weather/v1",
            method="invalid_method",
            params={},
            request_id="test-invalid"
        )
        
        assert response.success  # Router succeeds, but service returns error
        result = response.data["result"]
        assert result["is_error"]
        assert "Unknown method: invalid_method" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_service_status_handling(self):
        """Test handling of service status changes."""
        # Initially active
        response = await self.router.route_request(
            url="/weather/v1",
            method="get_weather_forecast",
            params={},
            request_id="test-status-1"
        )
        assert response.success
        
        # Set service to inactive
        self.service.set_status("inactive")
        
        response = await self.router.route_request(
            url="/weather/v1",
            method="get_weather_forecast",
            params={},
            request_id="test-status-2"
        )
        assert not response.success
        assert "currently inactive" in response.error
        
        # Reactivate service
        self.service.set_status("active")
        
        response = await self.router.route_request(
            url="/weather/v1",
            method="get_weather_forecast",
            params={},
            request_id="test-status-3"
        )
        assert response.success


if __name__ == "__main__":
    pytest.main([__file__])