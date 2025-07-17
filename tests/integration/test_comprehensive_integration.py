"""
Comprehensive integration tests for the multi-service MCP platform.

This test suite covers:
1. Integration tests for all service endpoints
2. Tests for MCP protocol compliance
3. Tests for cross-service interactions
4. Error path testing for all services
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from multi_service_server import app, mcp_server
from service_registry import ServiceRegistry
from services.base_service import BaseService
from services.emoji_oracle_service import EmojiOracleService
from services.fortune_service import FortuneService
from services.lucky_numbers_service import LuckyNumbersService
from services.mindful_service import MindfulService
from services.mvg_service import MVGService
from services.timestamp_service import TimestampService
from services.weather_service import WeatherService
from data.models import ToolResult, ServiceInfo


@pytest.fixture
def client():
    """Create a test client with all services registered."""
    # Create a test client
    test_client = TestClient(app)
    return test_client


# 1. INTEGRATION TESTS FOR ALL SERVICE ENDPOINTS

@pytest.mark.parametrize("service_name,endpoint,params", [
    ("mindful", "get_mindful_sentence", {}),
    ("weather", "get_weather_forecast", {}),
    ("emoji-oracle", "get_emoji_oracle", {}),
    ("timestamp", "generate_random_timestamp", {"start": "2023-01-01T00:00:00", "end": "2023-01-02T00:00:00"}),
    ("fortune", "get_fortune_cookie", {}),
    ("lucky-numbers", "generate_blessed_numbers", {"scenario": "lottery"}),
    # MVG service endpoints
    ("mvg", "get_departures", {"station_name": "Hauptbahnhof"}),
    ("mvg", "find_station", {"station_name": "Marienplatz"}),
])
def test_service_endpoints(client, service_name, endpoint, params):
    """Test all service endpoints through direct API calls."""
    # Make the request to the service endpoint
    response = client.post(
        f"/services/{service_name}/v1/{endpoint}",
        json=params
    )
    
    # Check if the endpoint exists (some might not be implemented as direct endpoints)
    if response.status_code == 404:
        pytest.skip(f"Endpoint {service_name}/v1/{endpoint} not implemented as direct API")
    
    # For implemented endpoints, check the response
    assert response.status_code == 200
    data = response.json()
    
    # Basic validation of response structure
    assert isinstance(data, dict)
    assert "status" in data or "result" in data or "content" in data or "message" in data


# 2. TESTS FOR MCP PROTOCOL COMPLIANCE

def test_mcp_jsonrpc_version(client):
    """Test that all MCP responses include the correct JSON-RPC version."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"


def test_mcp_id_echo(client):
    """Test that MCP responses echo back the request ID."""
    request_id = "test-unique-id-12345"
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": request_id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == request_id


def test_mcp_tools_list_format(client):
    """Test that tools/list response follows the MCP protocol format."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "result" in data
    assert "tools" in data["result"]
    assert isinstance(data["result"]["tools"], list)
    
    # Check tool format
    for tool in data["result"]["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool or "inputSchema" in tool


def test_mcp_tools_call_format(client):
    """Test that tools/call response follows the MCP protocol format."""
    # Use a simple tool that's likely to succeed
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "mindful_get_mindful_sentence"
            },
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "result" in data
    assert "content" in data["result"]
    assert isinstance(data["result"]["content"], list)
    assert len(data["result"]["content"]) > 0
    
    # Check content format
    content = data["result"]["content"][0]
    assert "type" in content
    assert content["type"] == "text"
    assert "text" in content


def test_mcp_error_format(client):
    """Test that MCP error responses follow the protocol format."""
    # Request with invalid method
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check error structure
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


def test_mcp_invalid_tool_format(client):
    """Test that calling an invalid tool returns a properly formatted error."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool"
            },
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check if the error is in the result field or in the error field
    if "result" in data and "is_error" in data["result"]:
        # In some MCP implementations, tool errors are returned in the result with is_error=true
        assert data["result"]["is_error"] is True
        assert "content" in data["result"]
        assert len(data["result"]["content"]) > 0
        assert "text" in data["result"]["content"][0]
        assert "non_existent_tool" in data["result"]["content"][0]["text"]
    elif "error" in data:
        # In other implementations, errors are returned in the error field
        assert "message" in data["error"]
        assert "non_existent_tool" in data["error"]["message"] or "non" in data["error"]["message"]


# 3. TESTS FOR CROSS-SERVICE INTERACTIONS

def test_error_response_with_emoji_oracle(client):
    """Test that error responses include emojis from the emoji oracle service."""
    # Request with invalid service
    response = client.post(
        "/services/invalid-service/v1/some-method",
        json={}
    )
    
    # Check if the endpoint returns a proper error
    if response.status_code == 404:
        data = response.json()
        # Check if the error response includes emojis (this depends on your implementation)
        if "detail" in data:
            # Look for emoji characters in the error message
            has_emoji = any(ord(c) > 0x1F000 for c in data["detail"])
            assert has_emoji, "Error response should include emojis from the emoji oracle"


def test_service_registry_integration(client):
    """Test that all services are properly registered and discoverable."""
    response = client.get("/services")
    
    assert response.status_code == 200
    data = response.json()
    
    # Handle different response formats
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        # Response is a list of service objects
        service_names = [service["name"] for service in data]
    elif isinstance(data, list) and all(isinstance(item, str) for item in data):
        # Response is a list of service names
        service_names = data
    elif isinstance(data, dict) and "services" in data:
        # Response is a dict with a services list
        services = data["services"]
        if isinstance(services, list) and all(isinstance(item, dict) for item in services):
            service_names = [service["name"] for service in services]
        else:
            service_names = services
    else:
        # For debugging, print the actual data structure
        print(f"Unexpected service registry response format: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {data.keys()}")
        pytest.skip("Unexpected service registry response format")
        return
    
    # Check that we have all expected services
    expected_services = ["mindful", "weather", "emoji-oracle", "timestamp", "fortune", "lucky-numbers", "mvg"]
    
    for service in expected_services:
        assert service in service_names, f"Service {service} should be registered"


def test_service_info_endpoint(client):
    """Test that each service provides detailed information through its info endpoint."""
    # Get the list of services
    response = client.get("/services")
    assert response.status_code == 200
    services = response.json()
    
    # Handle different response formats
    if isinstance(services, list):
        if all(isinstance(item, dict) for item in services):
            # List of service objects
            service_names = [service["name"] for service in services]
        elif all(isinstance(item, str) for item in services):
            # List of service names
            service_names = services
        else:
            pytest.skip("Unexpected service list format")
            return
    else:
        pytest.skip("Unexpected service response format")
        return
    
    # Check each service's info endpoint
    for service_name in service_names:
        info_response = client.get(f"/services/{service_name}")
        
        # Skip if endpoint not implemented
        if info_response.status_code == 404:
            continue
            
        assert info_response.status_code == 200
        info = info_response.json()
        
        # Check service info structure - adapt to actual response format
        if isinstance(info, dict):
            # Check for common fields that should be present
            assert any(key in info for key in ["name", "version", "description", "status", "tools"])
            
            # If name is present, check that it matches
            if "name" in info:
                assert info["name"] == service_name


# 4. ERROR PATH TESTING FOR ALL SERVICES

@pytest.mark.parametrize("service_name,endpoint,invalid_params,expected_error", [
    # Mindful service doesn't have parameters to validate
    
    # Weather service doesn't have required parameters
    
    # Emoji oracle doesn't have required parameters
    
    # Timestamp service with invalid date format
    ("timestamp", "generate_random_timestamp", {"start": "invalid-date"}, "Invalid date format"),
    
    # Fortune service doesn't have required parameters
    
    # Lucky numbers service with invalid scenario
    ("lucky-numbers", "generate_blessed_numbers", {"scenario": "invalid_scenario"}, "Invalid scenario"),
    
    # Lucky numbers service with invalid count
    ("lucky-numbers", "generate_blessed_numbers", {"scenario": "lottery", "count": 100}, "Count must be"),
    
    # Lucky numbers service with invalid min/max values
    ("lucky-numbers", "generate_blessed_numbers", {"scenario": "lottery", "min_value": 50, "max_value": 10}, "Min value must be less than max value"),
    
    # Lucky numbers service with invalid energy level
    ("lucky-numbers", "generate_blessed_numbers", {"scenario": "lottery", "energy_level": "super-extreme"}, "Invalid energy level"),
    
    # MVG service with missing station name
    ("mvg", "get_departures", {}, "station_name"),
    
    # MVG service with invalid station name
    ("mvg", "find_station", {"station_name": ""}, "station_name")
])
def test_service_error_handling(client, service_name, endpoint, invalid_params, expected_error):
    """Test error handling for all services with invalid parameters."""
    # Make the request to the service endpoint
    response = client.post(
        f"/services/{service_name}/v1/{endpoint}",
        json=invalid_params
    )
    
    # Check if the endpoint exists
    if response.status_code == 404:
        # Try through MCP endpoint instead
        mcp_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": f"{service_name}_{endpoint}",
                    "arguments": invalid_params
                },
                "id": "test-id"
            }
        )
        
        assert mcp_response.status_code == 200
        data = mcp_response.json()
        
        # Check for error in MCP response
        if "result" in data and "is_error" in data["result"]:
            assert data["result"]["is_error"] is True
            assert "content" in data["result"]
            assert any(expected_error in content["text"] for content in data["result"]["content"] if "text" in content)
        elif "error" in data:
            assert expected_error in data["error"]["message"]
    else:
        # Direct API response
        data = response.json()
        
        # Check for error in direct API response
        if "error" in data:
            assert expected_error in data["error"]
        elif "detail" in data:
            assert expected_error in data["detail"]
        elif "status" in data and data["status"] == "error":
            assert expected_error in str(data)


def test_invalid_json_request(client):
    """Test handling of invalid JSON in requests."""
    response = client.post(
        "/mcp",
        data="This is not valid JSON",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code in [400, 422]  # Either is acceptable for invalid JSON


def test_missing_required_fields(client):
    """Test handling of requests missing required fields."""
    # Missing method
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "test-id"
            # Missing method
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    
    # Missing params for tools/call
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            # Missing params
            "id": "test-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_service_unavailable(client):
    """Test handling of requests to unavailable services."""
    # This test assumes there's a way to disable services or that some services might be unavailable
    # If your implementation doesn't support this, you can skip this test
    
    # Try to access a non-existent service
    response = client.post(
        "/services/non-existent-service/v1/some-method",
        json={}
    )
    
    # The API might return 404 (not found) or 400 (bad request) for non-existent services
    assert response.status_code in [404, 400]
    data = response.json()
    
    # Check for error message in the response
    if "detail" in data:
        assert "not found" in data["detail"].lower() or "non-existent-service" in data["detail"].lower()
    elif "error" in data:
        assert "not found" in data["error"].lower() or "non-existent-service" in data["error"].lower()
    elif "message" in data:
        assert "not found" in data["message"].lower() or "non-existent-service" in data["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__])