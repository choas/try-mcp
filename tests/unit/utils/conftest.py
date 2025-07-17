"""
Utility-specific test fixtures and helpers.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Sample configuration data for testing
@pytest.fixture
def sample_config():
    """Fixture providing a sample configuration dictionary."""
    return {
        "services": {
            "mvg": {
                "enabled": True,
                "version": "v1",
                "rate_limit": 100
            },
            "mindful": {
                "enabled": True,
                "version": "v1",
                "sentences_per_day": 4
            },
            "weather": {
                "enabled": True,
                "version": "v1"
            },
            "emoji-oracle": {
                "enabled": True,
                "version": "v1"
            },
            "timestamp": {
                "enabled": True,
                "version": "v1"
            },
            "fortune": {
                "enabled": True,
                "version": "v1"
            },
            "lucky-numbers": {
                "enabled": True,
                "version": "v1"
            }
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8003,
            "log_level": "info"
        },
        "logging": {
            "file": "multi_service_platform.log",
            "level": "info",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }

@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Fixture providing a temporary configuration file."""
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(sample_config, f)
    return config_file

@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    env_vars = {
        "MCP_LOG_LEVEL": "debug",
        "MCP_PORT": "8004",
        "MCP_HOST": "localhost",
        "MCP_SERVICES_MVG_ENABLED": "true",
        "MCP_SERVICES_MINDFUL_ENABLED": "true"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    logger = MagicMock()
    return logger

# Helper functions for utility testing
def assert_config_loaded(config):
    """Assert that a configuration has been properly loaded."""
    assert "services" in config
    assert "server" in config
    assert "logging" in config
    
    assert "mvg" in config["services"]
    assert "mindful" in config["services"]
    assert "weather" in config["services"]
    
    assert "host" in config["server"]
    assert "port" in config["server"]
    assert "log_level" in config["server"]

def assert_service_enabled(config, service_name):
    """Assert that a service is enabled in the configuration."""
    assert service_name in config["services"]
    assert config["services"][service_name]["enabled"] is True

def assert_service_disabled(config, service_name):
    """Assert that a service is disabled in the configuration."""
    assert service_name in config["services"]
    assert config["services"][service_name]["enabled"] is False