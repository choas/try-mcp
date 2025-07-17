"""
Configuration for pytest with common fixtures and helpers.
"""

import os
import json
import asyncio
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from multi_service_server import app
from service_registry import ServiceRegistry
from services.base_service import BaseService
from data.models import ToolResult, ServiceInfo

# Enable asyncio for pytest
pytest_plugins = ["pytest_asyncio"]

# Fixed datetime for consistent test results
FIXED_DATETIME = datetime(2023, 1, 1, 12, 0)

# Mock function for datetime.now() to ensure consistent test results
def mock_datetime_now():
    """Return a fixed datetime for testing."""
    return FIXED_DATETIME

@pytest.fixture
def fixed_datetime():
    """Fixture providing a fixed datetime for testing."""
    return FIXED_DATETIME

@pytest.fixture
def test_client():
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def service_registry():
    """Fixture providing a clean ServiceRegistry instance."""
    registry = ServiceRegistry()
    return registry

@pytest.fixture
def mock_service():
    """Fixture providing a mock service for testing."""
    service = MagicMock(spec=BaseService)
    service.name = "mock-service"
    service.version = "v1"
    service.description = "Mock service for testing"
    service.get_service_info.return_value = ServiceInfo(
        name="mock-service",
        version="v1",
        description="Mock service for testing",
        tools=[],
        status="active"
    )
    service.handle_request.return_value = ToolResult(
        content=[{"type": "text", "text": "Mock response"}],
        is_error=False
    )
    return service

@pytest.fixture
def sample_tool_result():
    """Fixture providing a sample ToolResult for testing."""
    return ToolResult(
        content=[{"type": "text", "text": "Sample response"}],
        is_error=False
    )

@pytest.fixture
def error_tool_result():
    """Fixture providing an error ToolResult for testing."""
    return ToolResult(
        content=[{"type": "text", "text": "Error: Something went wrong"}],
        is_error=True
    )

@pytest.fixture
def sample_mcp_request():
    """Fixture providing a sample MCP request for testing."""
    return {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "service_method",
            "arguments": {"param1": "value1", "param2": "value2"}
        },
        "id": "test-id"
    }

@pytest.fixture
def sample_mcp_response():
    """Fixture providing a sample MCP response for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-id",
        "result": {
            "content": [
                {"type": "text", "text": "Sample response"}
            ],
            "is_error": False
        }
    }

@pytest.fixture
def sample_error_response():
    """Fixture providing a sample error response for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-id",
        "error": {
            "code": -32601,
            "message": "Method not found",
            "data": {"available_methods": ["method1", "method2"]}
        }
    }

# Helper functions for common test operations
def load_test_data(filename):
    """Load test data from a JSON file in the fixtures directory."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    file_path = os.path.join(fixtures_dir, filename)
    with open(file_path, "r") as f:
        return json.load(f)

def assert_tool_result_success(result):
    """Assert that a ToolResult represents a successful response."""
    assert isinstance(result, ToolResult)
    assert not result.is_error
    assert len(result.content) > 0
    assert result.content[0]["type"] == "text"

def assert_tool_result_error(result):
    """Assert that a ToolResult represents an error response."""
    assert isinstance(result, ToolResult)
    assert result.is_error
    assert len(result.content) > 0
    assert result.content[0]["type"] == "text"
    assert "Error" in result.content[0]["text"]

def assert_mcp_response_success(response):
    """Assert that an MCP response represents a successful response."""
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert "result" in response
    assert "content" in response["result"]

def assert_mcp_response_error(response):
    """Assert that an MCP response represents an error response."""
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert "error" in response
    assert "code" in response["error"]
    assert "message" in response["error"]