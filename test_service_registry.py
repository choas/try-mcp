"""Unit tests for the service registry."""

import pytest
from unittest.mock import patch, MagicMock

from service_registry import ServiceRegistry
from services.base_service import BaseService
from services.fortune_service import FortuneService
from services.mindful_service import MindfulService


class MockService(BaseService):
    """Mock service for testing."""
    
    def __init__(self, name="test", version="v1", description="Test service"):
        super().__init__(name, version, description)
    
    async def handle_request(self, method, params):
        return self._create_text_response("Mock response")
    
    def get_tools(self):
        return [{"name": "mock_tool", "description": "Mock tool", "inputSchema": {"type": "object", "properties": {}, "required": []}}]


class TestServiceRegistry:
    """Test cases for the ServiceRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ServiceRegistry()
    
    def test_registry_initialization(self):
        """Test that the registry initializes correctly."""
        assert len(self.registry._service_classes) == 0
        assert len(self.registry._service_instances) == 0
        assert self.registry.get_registered_service_names() == []
    
    def test_register_service_class(self):
        """Test registering a service class."""
        self.registry.register_service_class(MockService)
        
        # Should have registered the service class
        assert len(self.registry._service_classes) == 1
        assert "test_v1" in self.registry._service_classes
        assert self.registry._service_classes["test_v1"] == MockService
    
    def test_create_service_instance(self):
        """Test creating service instances."""
        # Register service class first
        self.registry.register_service_class(MockService)
        
        # Create instance
        instance = self.registry.create_service_instance("test", "v1")
        
        assert instance is not None
        assert isinstance(instance, MockService)
        assert instance.name == "test"
        assert instance.version == "v1"
        
        # Should cache the instance
        assert len(self.registry._service_instances) == 1
        
        # Second call should return same instance
        instance2 = self.registry.create_service_instance("test", "v1")
        assert instance is instance2
    
    def test_create_nonexistent_service_instance(self):
        """Test creating instance of non-registered service."""
        instance = self.registry.create_service_instance("nonexistent", "v1")
        assert instance is None
    
    def test_get_all_service_instances(self):
        """Test getting all service instances."""
        # Register multiple service classes
        self.registry.register_service_class(MockService)
        
        class AnotherMockService(BaseService):
            def __init__(self):
                super().__init__("another", "v1", "Another test service")
            async def handle_request(self, method, params):
                return self._create_text_response("Another response")
            def get_tools(self):
                return []
        
        self.registry.register_service_class(AnotherMockService)
        
        # Get all instances
        instances = self.registry.get_all_service_instances()
        
        assert len(instances) == 2
        service_names = [instance.name for instance in instances]
        assert "test" in service_names
        assert "another" in service_names
    
    def test_load_services_from_config(self):
        """Test loading services from configuration."""
        config = [
            {"module": "services.fortune_service", "class": "FortuneService"},
            {"module": "services.mindful_service", "class": "MindfulService"}
        ]
        
        services = self.registry.load_services_from_config(config)
        
        assert len(services) == 2
        service_names = [service.name for service in services]
        assert "fortune" in service_names
        assert "mindful" in service_names
    
    def test_load_services_from_invalid_config(self):
        """Test loading services with invalid configuration."""
        config = [
            {"module": "nonexistent.module", "class": "NonexistentService"},
            {"module": "services.fortune_service", "class": "NonexistentClass"}
        ]
        
        services = self.registry.load_services_from_config(config)
        
        # Should handle errors gracefully and return empty list
        assert len(services) == 0
    
    def test_auto_discover_services(self):
        """Test auto-discovery of services."""
        services = self.registry.auto_discover_services()
        
        # Should discover the available services
        assert len(services) > 0
        
        service_names = [service.name for service in services]
        # Should include fortune service (and others if available)
        assert "fortune" in service_names
    
    def test_auto_discover_with_missing_modules(self):
        """Test auto-discovery handles missing modules gracefully."""
        # Mock importlib to simulate missing modules
        with patch('service_registry.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            services = self.registry.auto_discover_services()
            
            # Should handle errors gracefully
            assert len(services) == 0
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        # Register some services
        self.registry.register_service_class(MockService)
        self.registry.create_service_instance("test", "v1")
        
        assert len(self.registry._service_classes) > 0
        assert len(self.registry._service_instances) > 0
        
        # Clear registry
        self.registry.clear_registry()
        
        assert len(self.registry._service_classes) == 0
        assert len(self.registry._service_instances) == 0
        assert self.registry.get_registered_service_names() == []
    
    def test_get_registered_service_names(self):
        """Test getting registered service names."""
        # Initially empty
        assert self.registry.get_registered_service_names() == []
        
        # Register services
        self.registry.register_service_class(MockService)
        
        class AnotherService(BaseService):
            def __init__(self):
                super().__init__("another", "v2", "Another service")
            async def handle_request(self, method, params):
                return self._create_text_response("Response")
            def get_tools(self):
                return []
        
        self.registry.register_service_class(AnotherService)
        
        names = self.registry.get_registered_service_names()
        assert len(names) == 2
        assert "test_v1" in names
        assert "another_v2" in names


class TestServiceRegistryIntegration:
    """Integration tests for service registry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ServiceRegistry()
    
    def test_full_workflow(self):
        """Test the complete service registry workflow."""
        # 1. Auto-discover services
        services = self.registry.auto_discover_services()
        assert len(services) > 0
        
        # 2. Check that fortune service was discovered
        fortune_services = [s for s in services if s.name == "fortune"]
        assert len(fortune_services) == 1
        fortune_service = fortune_services[0]
        
        # 3. Verify service functionality
        assert fortune_service.supports_prompts()
        prompts = fortune_service.get_prompts()
        assert len(prompts) == 30
        
        # 4. Test service instance caching
        cached_service = self.registry.create_service_instance("fortune", "v1")
        assert cached_service is fortune_service
    
    def test_registry_with_multi_service_server(self):
        """Test service registry integration with multi-service server."""
        from multi_service_server import MultiServiceMCPServer
        
        # Create server with custom registry
        custom_registry = ServiceRegistry()
        server = MultiServiceMCPServer(service_registry=custom_registry)
        
        # Should have discovered and registered services
        assert server.router.get_service_count() > 0
        
        # Should have fortune service
        fortune_service = server.router.get_service("fortune", "v1")
        assert fortune_service is not None
        assert fortune_service.name == "fortune"
    
    def test_service_registry_error_handling(self):
        """Test error handling in service registry."""
        # Test with malformed config
        config = [
            {"module": "services.fortune_service"},  # Missing class
            {"class": "FortuneService"},  # Missing module
            {}  # Empty config
        ]
        
        services = self.registry.load_services_from_config(config)
        assert len(services) == 0  # Should handle errors gracefully
    
    def test_service_registry_extensibility(self):
        """Test that service registry is extensible."""
        # Create a custom service
        class CustomService(BaseService):
            def __init__(self):
                super().__init__("custom", "v1", "Custom test service")
            
            async def handle_request(self, method, params):
                return self._create_text_response("Custom response")
            
            def get_tools(self):
                return [{"name": "custom_tool", "description": "Custom tool", "inputSchema": {"type": "object", "properties": {}, "required": []}}]
            
            def supports_prompts(self):
                return True
            
            def get_prompts(self):
                return [{"name": "custom_prompt", "description": "Custom prompt", "arguments": []}]
        
        # Register custom service
        self.registry.register_service_class(CustomService)
        
        # Create instance
        custom_service = self.registry.create_service_instance("custom", "v1")
        assert custom_service is not None
        assert custom_service.name == "custom"
        assert custom_service.supports_prompts()
        
        # Test with multi-service server
        from multi_service_server import MultiServiceMCPServer
        server = MultiServiceMCPServer(service_registry=self.registry)
        
        # Should include custom service
        custom_registered = server.router.get_service("custom", "v1")
        assert custom_registered is not None
        assert custom_registered.name == "custom"