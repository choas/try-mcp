"""Configuration management for the multi-service MCP platform."""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Set

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for the multi-service MCP platform.
    
    This class handles loading configuration from files and environment variables,
    and provides access to configuration values.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "server": {
            "host": "0.0.0.0",
            "port": 8003,
            "debug": False,
            "log_level": "info",
            "allow_public_service_control": False  # Default to false for security
        },
        "services": {
            # Default all services to enabled
            "enabled_services": ["*"],  # "*" means all services are enabled
            "disabled_services": []     # Explicitly disabled services
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file. If None, default configuration is used.
        """
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
        
        # Override with environment variables
        self._load_from_env()
        
        logger.info(f"Configuration loaded: {self._config}")
    
    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file.
        """
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                
            # Merge with default configuration
            self._merge_config(file_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Server configuration
        if os.getenv('MCP_HOST'):
            self._config['server']['host'] = os.getenv('MCP_HOST')
        
        if os.getenv('MCP_PORT'):
            try:
                self._config['server']['port'] = int(os.getenv('MCP_PORT'))
            except ValueError:
                logger.warning(f"Invalid port in environment variable: {os.getenv('MCP_PORT')}")
        
        if os.getenv('MCP_DEBUG'):
            self._config['server']['debug'] = os.getenv('MCP_DEBUG').lower() in ('true', '1', 'yes')
        
        if os.getenv('MCP_LOG_LEVEL'):
            self._config['server']['log_level'] = os.getenv('MCP_LOG_LEVEL').lower()
        
        # Service configuration
        if os.getenv('MCP_ENABLED_SERVICES'):
            self._config['services']['enabled_services'] = os.getenv('MCP_ENABLED_SERVICES').split(',')
        
        if os.getenv('MCP_DISABLED_SERVICES'):
            self._config['services']['disabled_services'] = os.getenv('MCP_DISABLED_SERVICES').split(',')
    
    def _merge_config(self, config: Dict[str, Any]) -> None:
        """Merge configuration with the current configuration.
        
        Args:
            config: Configuration to merge.
        """
        for section, values in config.items():
            if section not in self._config:
                self._config[section] = {}
            
            if isinstance(values, dict):
                for key, value in values.items():
                    self._config[section][key] = value
            else:
                self._config[section] = values
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            section: Configuration section.
            key: Configuration key. If None, the entire section is returned.
            default: Default value if the key is not found.
            
        Returns:
            Configuration value or default if not found.
        """
        if section not in self._config:
            return default
        
        if key is None:
            return self._config[section]
        
        return self._config[section].get(key, default)
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled.
        
        Args:
            service_name: Name of the service to check.
            
        Returns:
            True if the service is enabled, False otherwise.
        """
        enabled_services = self.get('services', 'enabled_services', ['*'])
        disabled_services = self.get('services', 'disabled_services', [])
        
        # If service is explicitly disabled, it's disabled
        if service_name in disabled_services:
            return False
        
        # If all services are enabled or this service is explicitly enabled, it's enabled
        return '*' in enabled_services or service_name in enabled_services
    
    def get_enabled_services(self, available_services: List[str]) -> List[str]:
        """Get the list of enabled services.
        
        Args:
            available_services: List of available service names.
            
        Returns:
            List of enabled service names.
        """
        return [service for service in available_services if self.is_service_enabled(service)]
    
    def get_disabled_services(self, available_services: List[str]) -> List[str]:
        """Get the list of disabled services.
        
        Args:
            available_services: List of available service names.
            
        Returns:
            List of disabled service names.
        """
        return [service for service in available_services if not self.is_service_enabled(service)]
    
    def is_public_service_control_allowed(self) -> bool:
        """Check if public service control is allowed.
        
        Returns:
            True if public service control is allowed, False otherwise.
        """
        return self.get('server', 'allow_public_service_control', False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            Configuration as a dictionary.
        """
        return self._config.copy()