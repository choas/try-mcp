"""Integration tests for the random timestamp service."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
import json

from services.timestamp_service import TimestampService
from service_router import ServiceRouter


@pytest.fixture
def timestamp_service():
    """Create a timestamp service instance for testing."""
    return TimestampService()


@pytest.fixture
def service_router(timestamp_service):
    """Create a service router with the timestamp service registered."""
    router = ServiceRouter()
    router.register_service(timestamp_service)
    return router


@pytest.mark.asyncio
async def test_service_registration(service_router):
    """Test that the timestamp service is properly registered with the router."""
    services = service_router.list_services()
    
    # Check that timestamp service is registered
    assert any(service.name == "timestamp" for service in services)
    
    # Check that the service info is correct
    service = service_router.get_service("timestamp", "v1")
    assert service is not None
    assert service.name == "timestamp"
    assert service.version == "v1"
    assert "Random timestamp generator" in service.description


@pytest.mark.asyncio
async def test_route_timestamp_request(service_router):
    """Test routing a request to the timestamp service."""
    # Route the request
    response = await service_router.route_request(
        url="/timestamp/v1",
        method="generate_random_timestamp",
        params={},
        request_id="test-request-1"
    )
    
    # Check that the response is successful
    assert response is not None
    assert response.success
    
    # Check that the response contains a timestamp
    result = response.data["result"]
    assert not result["is_error"]
    
    response_text = result["content"][0]["text"]
    assert "ISO 8601:" in response_text
    assert "Range:" in response_text


@pytest.mark.asyncio
async def test_timestamp_with_custom_range(service_router):
    """Test generating a timestamp with a custom range through the router."""
    # Define custom range
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(days=3)
    
    # Route the request with custom parameters
    response = await service_router.route_request(
        url="/timestamp/v1",
        method="generate_random_timestamp",
        params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        request_id="test-request-2"
    )
    
    # Check that the response is successful
    assert response is not None
    assert response.success
    
    # Extract timestamp from response text
    result = response.data["result"]
    assert not result["is_error"]
    
    response_text = result["content"][0]["text"]
    lines = response_text.split('\n')
    iso_line = [line for line in lines if "ISO 8601:" in line][0]
    timestamp_str = iso_line.split("ISO 8601:")[1].strip()
    
    # Parse the timestamp to ensure it's valid
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Verify it's within the specified range
    assert start_time <= timestamp <= end_time


@pytest.mark.asyncio
async def test_invalid_service_version(service_router):
    """Test handling of invalid service version."""
    # Route the request with invalid version
    response = await service_router.route_request(
        url="/timestamp/v2",  # Invalid version
        method="generate_random_timestamp",
        params={},
        request_id="test-request-3"
    )
    
    # Check that the response is an error
    assert response is not None
    assert not response.success
    assert "version" in response.error.lower()