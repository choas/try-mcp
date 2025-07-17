"""Unit tests for the configuration manager."""

import os
import json
import tempfile
import pytest
from utils.config_manager import ConfigManager


def test_default_config():
    """Test that the default configuration is loaded correctly."""
    config = ConfigManager()
    
    # Check server configuration
    assert config.get('server', 'host') == '0.0.0.0'
    assert config.get('server', 'port') == 8003
    assert config.get('server', 'debug') is False
    assert config.get('server', 'log_level') == 'info'
    
    # Check service configuration
    assert config.get('services', 'enabled_services') == ['*']
    assert config.get('services', 'disabled_services') == []


def test_config_from_file():
    """Test loading configuration from a file."""
    # Create a temporary configuration file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        json.dump({
            'server': {
                'host': '127.0.0.1',
                'port': 9000
            },
            'services': {
                'enabled_services': ['service1', 'service2'],
                'disabled_services': ['service3']
            }
        }, f)
        config_file = f.name
    
    try:
        # Load configuration from file
        config = ConfigManager(config_file)
        
        # Check server configuration
        assert config.get('server', 'host') == '127.0.0.1'
        assert config.get('server', 'port') == 9000
        assert config.get('server', 'debug') is False  # Default value
        assert config.get('server', 'log_level') == 'info'  # Default value
        
        # Check service configuration
        assert config.get('services', 'enabled_services') == ['service1', 'service2']
        assert config.get('services', 'disabled_services') == ['service3']
    finally:
        # Clean up
        os.unlink(config_file)


def test_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    # Set environment variables
    monkeypatch.setenv('MCP_HOST', '192.168.1.1')
    monkeypatch.setenv('MCP_PORT', '8080')
    monkeypatch.setenv('MCP_DEBUG', 'true')
    monkeypatch.setenv('MCP_LOG_LEVEL', 'debug')
    monkeypatch.setenv('MCP_ENABLED_SERVICES', 'service1,service2')
    monkeypatch.setenv('MCP_DISABLED_SERVICES', 'service3,service4')
    
    # Load configuration
    config = ConfigManager()
    
    # Check server configuration
    assert config.get('server', 'host') == '192.168.1.1'
    assert config.get('server', 'port') == 8080
    assert config.get('server', 'debug') is True
    assert config.get('server', 'log_level') == 'debug'
    
    # Check service configuration
    assert config.get('services', 'enabled_services') == ['service1', 'service2']
    assert config.get('services', 'disabled_services') == ['service3', 'service4']


def test_is_service_enabled():
    """Test checking if a service is enabled."""
    # Create a configuration with specific enabled and disabled services
    config = ConfigManager()
    config._config['services']['enabled_services'] = ['service1', 'service2']
    config._config['services']['disabled_services'] = ['service3']
    
    # Check enabled services
    assert config.is_service_enabled('service1') is True
    assert config.is_service_enabled('service2') is True
    
    # Check disabled service
    assert config.is_service_enabled('service3') is False
    
    # Check unknown service (should be disabled)
    assert config.is_service_enabled('service4') is False
    
    # Test with wildcard enabled
    config._config['services']['enabled_services'] = ['*']
    assert config.is_service_enabled('service4') is True
    
    # But explicitly disabled services should still be disabled
    assert config.is_service_enabled('service3') is False


def test_get_enabled_disabled_services():
    """Test getting lists of enabled and disabled services."""
    # Create a configuration with specific enabled and disabled services
    config = ConfigManager()
    config._config['services']['enabled_services'] = ['service1', 'service2']
    config._config['services']['disabled_services'] = ['service3']
    
    available_services = ['service1', 'service2', 'service3', 'service4']
    
    # Check enabled services
    enabled = config.get_enabled_services(available_services)
    assert 'service1' in enabled
    assert 'service2' in enabled
    assert 'service3' not in enabled
    assert 'service4' not in enabled
    
    # Check disabled services
    disabled = config.get_disabled_services(available_services)
    assert 'service1' not in disabled
    assert 'service2' not in disabled
    assert 'service3' in disabled
    assert 'service4' in disabled
    
    # Test with wildcard enabled
    config._config['services']['enabled_services'] = ['*']
    
    enabled = config.get_enabled_services(available_services)
    assert 'service1' in enabled
    assert 'service2' in enabled
    assert 'service3' not in enabled  # Still disabled explicitly
    assert 'service4' in enabled
    
    disabled = config.get_disabled_services(available_services)
    assert 'service1' not in disabled
    assert 'service2' not in disabled
    assert 'service3' in disabled
    assert 'service4' not in disabled