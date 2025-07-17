"""Service registry for dynamic service loading and management."""

import importlib
import logging
from typing import Dict, List, Type, Optional
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for managing service plugins dynamically."""
    
    def __init__(self):
        """Initialize the service registry."""
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_instances: Dict[str, BaseService] = {}
    
    def register_service_class(self, service_class: Type[BaseService]) -> None:
        """Register a service class.
        
        Args:
            service_class: Service class to register
        """
        # Create a temporary instance to get the service name
        temp_instance = service_class()
        service_key = f"{temp_instance.name}_{temp_instance.version}"
        
        self._service_classes[service_key] = service_class
        logger.info(f"Registered service class: {service_key}")
    
    def create_service_instance(self, service_name: str, version: str) -> Optional[BaseService]:
        """Create an instance of a registered service.
        
        Args:
            service_name: Name of the service
            version: Version of the service
            
        Returns:
            Service instance or None if not found
        """
        service_key = f"{service_name}_{version}"
        
        if service_key in self._service_classes:
            if service_key not in self._service_instances:
                self._service_instances[service_key] = self._service_classes[service_key]()
                logger.info(f"Created service instance: {service_key}")
            
            return self._service_instances[service_key]
        
        return None
    
    def get_all_service_instances(self) -> List[BaseService]:
        """Get all registered service instances.
        
        Returns:
            List of all service instances
        """
        # Create instances for all registered classes
        instances = []
        for service_key, service_class in self._service_classes.items():
            if service_key not in self._service_instances:
                self._service_instances[service_key] = service_class()
            instances.append(self._service_instances[service_key])
        
        return instances
    
    def load_services_from_config(self, service_configs: List[Dict]) -> List[BaseService]:
        """Load services from configuration.
        
        Args:
            service_configs: List of service configuration dictionaries
                Each config should have: {"module": "services.service_name", "class": "ServiceClass"}
            
        Returns:
            List of loaded service instances
        """
        loaded_services = []
        
        for config in service_configs:
            try:
                module_name = config["module"]
                class_name = config["class"]
                
                # Import the module
                module = importlib.import_module(module_name)
                
                # Get the service class
                service_class = getattr(module, class_name)
                
                # Register and create instance
                self.register_service_class(service_class)
                
                # Create instance
                temp_instance = service_class()
                service_instance = self.create_service_instance(temp_instance.name, temp_instance.version)
                
                if service_instance:
                    loaded_services.append(service_instance)
                    logger.info(f"Loaded service: {temp_instance.name} v{temp_instance.version}")
                
            except Exception as e:
                logger.error(f"Failed to load service from config {config}: {e}")
        
        return loaded_services
    
    def auto_discover_services(self) -> List[BaseService]:
        """Auto-discover services in the services directory.
        
        Returns:
            List of discovered service instances
        """
        discovered_services = []
        
        # Common service modules to try
        service_modules = [
            {"module": "services.mvg_service", "class": "MVGService"},
            {"module": "services.mindful_service", "class": "MindfulService"},
            {"module": "services.emoji_oracle_service", "class": "EmojiOracleService"},
            {"module": "services.fortune_service", "class": "FortuneService"},
            {"module": "services.timestamp_service", "class": "TimestampService"},
        ]
        
        for service_config in service_modules:
            try:
                module_name = service_config["module"]
                class_name = service_config["class"]
                
                # Try to import the module
                module = importlib.import_module(module_name)
                service_class = getattr(module, class_name)
                
                # Register and create instance
                self.register_service_class(service_class)
                
                # Create instance
                temp_instance = service_class()
                service_instance = self.create_service_instance(temp_instance.name, temp_instance.version)
                
                if service_instance:
                    discovered_services.append(service_instance)
                    logger.info(f"Auto-discovered service: {temp_instance.name} v{temp_instance.version}")
                
            except ImportError:
                logger.debug(f"Service module not found: {service_config['module']}")
            except Exception as e:
                logger.warning(f"Failed to auto-discover service {service_config}: {e}")
        
        return discovered_services
    
    def get_registered_service_names(self) -> List[str]:
        """Get list of registered service names.
        
        Returns:
            List of service names
        """
        return list(self._service_classes.keys())
    
    def clear_registry(self) -> None:
        """Clear all registered services."""
        self._service_classes.clear()
        self._service_instances.clear()
        logger.info("Service registry cleared")