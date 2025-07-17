"""
Integration test fixtures and helpers.
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

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
def test_client():
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def mock_service_registry():
    """Fixture providing a mock ServiceRegistry with all services registered."""
    registry = ServiceRegistry()
    
    # Register all services
    registry.register_service(EmojiOracleService())
    registry.register_service(FortuneService())
    registry.register_service(LuckyNumbersService())
    registry.register_service(MindfulService())
    registry.register_service(MVGService())
    registry.register_service(TimestampService())
    registry.register_service(WeatherService())
    
    return registry

@pytest.fixture
def mock_mcp_server(mock_service_registry):
    """Fixture providing a mock MCP server with the service registry."""
    server = MagicMock()
    server.router = mock_service_registry
    return server

@pytest.fixture
def sample_mcp_tools_list_request():
    """Fixture providing a sample MCP tools/list request."""
    return {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": "test-id"
    }

@pytest.fixture
def sample_mcp_tools_call_request():
    """Fixture providing a sample MCP tools/call request."""
    return {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "lucky-numbers_generate_blessed_numbers",
            "arguments": {
                "scenario": "lottery",
                "count": 5,
                "min_value": 1,
                "max_value": 49,
                "energy_level": "medium"
            }
        },
        "id": "test-id"
    }

@pytest.fixture
def sample_mcp_prompts_list_request():
    """Fixture providing a sample MCP prompts/list request."""
    return {
        "jsonrpc": "2.0",
        "method": "prompts/list",
        "id": "test-id"
    }

@pytest.fixture
def sample_service_endpoint_request():
    """Fixture providing a sample service endpoint request."""
    return {
        "scenario": "lottery",
        "count": 5,
        "min_value": 1,
        "max_value": 49,
        "energy_level": "medium"
    }

# Helper functions for integration testing
def assert_mcp_response_format(response):
    """Assert that an MCP response has the correct format."""
    assert response.status_code == 200
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data

def assert_tools_list_response(response):
    """Assert that a tools/list response has the correct format."""
    assert_mcp_response_format(response)
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    assert isinstance(data["result"]["tools"], list)
    assert len(data["result"]["tools"]) > 0
    
    # Check that each tool has the required fields
    for tool in data["result"]["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool or "inputSchema" in tool

def assert_tools_call_response(response):
    """Assert that a tools/call response has the correct format."""
    assert_mcp_response_format(response)
    data = response.json()
    assert "result" in data
    assert "content" in data["result"]
    assert isinstance(data["result"]["content"], list)
    assert len(data["result"]["content"]) > 0
    assert "is_error" in data["result"]

def assert_service_endpoint_response(response):
    """Assert that a service endpoint response has the correct format."""
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # The exact fields will depend on the service, but we can check some common ones
    assert "status" in data or "result" in data or "content" in data