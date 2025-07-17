"""Unit tests for service enablement functionality."""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from multi_service_server import app, MultiServiceMCPServer
from service_registry import ServiceRegistry
from services.base_service import BaseService
from utils.config_manager import ConfigManager


class MockService(BaseService):
    """Mock service for testing."""
    
    def __init__(self, name="mock-service", version="v1", description="Mock service for testing"):
        super().__init__(name, version, description)
    
    async def handle_request(self, method, params):
        """Mock handle_request method."""
        return {"result": "mock result"}
    
    def get_tools(self):
        """Mock get_tools method."""
        return [{"name": "mock_tool", "description": "Mock tool"}]


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = ConfigManager()
    # Override the configuration for testing
    config._config = {
        "server": {
            "host": "127.0.0.1",
            "port": 8003,
            "debug": False,
            "log_level": "info"
        },
        "services": {
            "enabled_services": ["service1", "service2"],
            "disabled_services": ["service3"]
        }
    }
    return config


@pytest.fixture
def mock_server(mock_config):
    """Create a mock server with mock services."""
    # Create mock services
    service1 = MockService(name="service1", version="v1", description="Service 1")
    service2 = MockService(name="service2", version="v1", description="Service 2")
    service3 = MockService(name="service3", version="v1", description="Service 3")
    service4 = MockService(name="service4", version="v1", description="Service 4")
    
    # Create a mock registry
    registry = ServiceRegistry()
    registry.register_service_class(MockService)
    
    # Create a server with the mock registry and config
    server = MultiServiceMCPServer(service_registry=registry, config_manager=mock_config)
    
    # Add services to the server
    server.add_service(service1)
    server.add_service(service2)
    server.add_service(service3)
    server.add_service(service4)
    
    return server


@pytest.fixture
def client(mock_server):
    """Create a test client with the mock server."""
    # Patch the global mcp_server in multi_service_server.py
    with patch('multi_service_server.mcp_server', mock_server):
        # Create a test client
        test_client = TestClient(app)
        yield test_client


def test_list_services(client):
    """Test listing all services."""
    response = client.get("/services")
    assert response.status_code == 200
    
    data = response.json()
    assert "services" in data
    # There might be a mock-service instance created by the MockService class
    assert len(data["services"]) >= 4
    
    # Check that service1 and service2 are active, service3 is inactive
    service1 = next((s for s in data["services"] if s["name"] == "service1"), None)
    service2 = next((s for s in data["services"] if s["name"] == "service2"), None)
    service3 = next((s for s in data["services"] if s["name"] == "service3"), None)
    service4 = next((s for s in data["services"] if s["name"] == "service4"), None)
    
    assert service1 is not None
    assert service2 is not None
    assert service3 is not None
    assert service4 is not None
    
    assert service1["status"] == "active"
    assert service2["status"] == "active"
    assert service3["status"] == "inactive"
    assert service4["status"] == "inactive"  # Not in enabled_services list


def test_get_service_info(client):
    """Test getting information about a specific service."""
    response = client.get("/services/service1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "service1"
    assert data["status"] == "active"
    
    response = client.get("/services/service3")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "service3"
    assert data["status"] == "inactive"


def test_enable_service(client):
    """Test enabling a service."""
    # Enable service3 (which is initially disabled)
    response = client.post("/services/service3/enable")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Service 'service3' enabled"
    
    # Check that service3 is now active
    response = client.get("/services/service3")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "service3"
    assert data["status"] == "active"


def test_disable_service(client):
    """Test disabling a service."""
    # Disable service1 (which is initially enabled)
    response = client.post("/services/service1/disable")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Service 'service1' disabled"
    
    # Check that service1 is now inactive
    response = client.get("/services/service1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "service1"
    assert data["status"] == "inactive"


def test_enable_nonexistent_service(client):
    """Test enabling a service that doesn't exist."""
    response = client.post("/services/nonexistent/enable")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_disable_nonexistent_service(client):
    """Test disabling a service that doesn't exist."""
    response = client.post("/services/nonexistent/disable")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    
    # Check that the services are in the health check response
    # The format might be service1_vv1 instead of service1_v1
    service1_key = next((k for k in data["services"].keys() if k.startswith("service1_")), None)
    service2_key = next((k for k in data["services"].keys() if k.startswith("service2_")), None)
    service3_key = next((k for k in data["services"].keys() if k.startswith("service3_")), None)
    service4_key = next((k for k in data["services"].keys() if k.startswith("service4_")), None)
    
    assert service1_key is not None, "service1 not found in health check"
    assert service2_key is not None, "service2 not found in health check"
    assert service3_key is not None, "service3 not found in health check"
    assert service4_key is not None, "service4 not found in health check"
    
    assert data["services"][service1_key] == "active"
    assert data["services"][service2_key] == "active"
    assert data["services"][service3_key] == "inactive"
    assert data["services"][service4_key] == "inactive"