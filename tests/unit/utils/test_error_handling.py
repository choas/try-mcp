"""Unit tests for error handling and response formatting."""

import pytest
import json
from unittest.mock import MagicMock, patch

from utils.error_formatter import ErrorFormatter, ErrorCode, ErrorHandler
from service_router import ServiceRouter
from services.base_service import BaseService
from data.models import ToolResult


class TestErrorFormatter:
    """Test cases for the ErrorFormatter utility."""
    
    def test_format_error_basic(self):
        """Test basic error formatting."""
        error = ErrorFormatter.format_error(
            code=ErrorCode.INVALID_PARAMS,
            message="Invalid parameter",
            request_id="test-123"
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == "test-123"
        assert error["error"]["code"] == ErrorCode.INVALID_PARAMS.value
        assert error["error"]["message"] == "Invalid parameter"
    
    def test_format_error_with_data(self):
        """Test error formatting with additional data."""
        error = ErrorFormatter.format_error(
            code=ErrorCode.SERVICE_NOT_FOUND,
            message="Service not found",
            data={"service": "test", "available_services": ["a", "b"]},
            request_id="test-456"
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == "test-456"
        assert error["error"]["code"] == ErrorCode.SERVICE_NOT_FOUND.value
        assert error["error"]["message"] == "Service not found"
        assert error["error"]["data"]["service"] == "test"
        assert "available_services" in error["error"]["data"]
    
    def test_service_not_found_error(self):
        """Test service not found error helper."""
        error = ErrorFormatter.service_not_found_error(
            service_name="test",
            available_services=["a", "b"],
            request_id="test-789"
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == "test-789"
        assert error["error"]["code"] == ErrorCode.SERVICE_NOT_FOUND.value
        assert "test" in error["error"]["message"]
        assert error["error"]["data"]["service"] == "test"
        assert error["error"]["data"]["available_services"] == ["a", "b"]
    
    def test_version_not_supported_error(self):
        """Test version not supported error helper."""
        error = ErrorFormatter.version_not_supported_error(
            service_name="test",
            version="v2",
            available_versions=["v1", "v3"],
            request_id="test-abc"
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == "test-abc"
        assert error["error"]["code"] == ErrorCode.VERSION_NOT_SUPPORTED.value
        assert "test" in error["error"]["message"]
        assert "v2" in error["error"]["message"]
        assert error["error"]["data"]["service"] == "test"
        assert error["error"]["data"]["version"] == "v2"
        assert error["error"]["data"]["available_versions"] == ["v1", "v3"]


class TestErrorHandler:
    """Test cases for the ErrorHandler utility."""
    
    @patch("utils.error_formatter.logger")
    def test_log_error(self, mock_logger):
        """Test error logging."""
        ErrorHandler.log_error(
            error_type="TEST_ERROR",
            message="Test error message",
            context={"test": "data"}
        )
        
        mock_logger.error.assert_called_once()
        # Check that the error message contains the error type
        assert "TEST_ERROR" in mock_logger.error.call_args[0][0]
        # Check that the context was passed as extra data
        assert "context" in mock_logger.error.call_args[1]["extra"]
    
    @patch("utils.error_formatter.logger")
    def test_handle_exception(self, mock_logger):
        """Test exception handling."""
        exception = ValueError("Test exception")
        
        error_response, log_data = ErrorHandler.handle_exception(
            exception=exception,
            error_type="TEST_EXCEPTION",
            context={"test": "context"},
            request_id="test-def"
        )
        
        # Check that the exception was logged
        mock_logger.error.assert_called_once()
        
        # Check the error response format
        assert error_response["jsonrpc"] == "2.0"
        assert error_response["id"] == "test-def"
        assert error_response["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
        assert "Test exception" in error_response["error"]["message"]
        
        # Check the log data
        assert log_data["error_type"] == "TEST_EXCEPTION"
        assert "Test exception" in log_data["error_message"]  # Changed from 'message' to 'error_message'
        assert log_data["exception"] == "ValueError"
        assert log_data["context"]["test"] == "context"
        
        # Ensure we're not using 'message' key to avoid conflicts with Python's logging system
        assert 'message' not in log_data


@pytest.mark.asyncio
class TestServiceRouterErrorHandling:
    """Test cases for error handling in the ServiceRouter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = ServiceRouter()
    
    async def test_invalid_url_format(self):
        """Test handling of invalid URL format."""
        response = await self.router.route_request(
            url="invalid-url",
            method="test_method",
            params={},
            request_id="test-url"
        )
        
        assert not response.success
        assert "Invalid URL format" in response.error
        assert "error_code" in response.data
        assert response.data["error_code"] == ErrorCode.INVALID_URL_FORMAT.value
    
    async def test_service_not_found(self):
        """Test handling of non-existent service."""
        response = await self.router.route_request(
            url="/nonexistent/v1",
            method="test_method",
            params={},
            request_id="test-service"
        )
        
        assert not response.success
        assert "not found" in response.error
        assert "error_code" in response.data
        assert response.data["error_code"] == ErrorCode.SERVICE_NOT_FOUND.value
        assert "available_services" in response.data
    
    async def test_service_error(self):
        """Test handling of service errors."""
        # Create a mock service that raises an exception
        mock_service = MagicMock(spec=BaseService)
        mock_service.name = "mock"
        mock_service.version = "v1"
        mock_service.get_status.return_value = "active"
        mock_service.handle_request.side_effect = ValueError("Test service error")
        
        # Register the mock service
        self.router.register_service(mock_service)
        
        response = await self.router.route_request(
            url="/mock/v1",
            method="test_method",
            params={},
            request_id="test-error"
        )
        
        assert not response.success
        assert "Service error" in response.error
        assert "error_code" in response.data
        assert response.data["error_code"] == ErrorCode.SERVICE_ERROR.value
    
    async def test_inactive_service(self):
        """Test handling of inactive service."""
        # Create a mock service with inactive status
        mock_service = MagicMock(spec=BaseService)
        mock_service.name = "inactive"
        mock_service.version = "v1"
        mock_service.get_status.return_value = "inactive"
        
        # Register the mock service
        self.router.register_service(mock_service)
        
        response = await self.router.route_request(
            url="/inactive/v1",
            method="test_method",
            params={},
            request_id="test-inactive"
        )
        
        assert not response.success
        assert "currently inactive" in response.error
        assert "error_code" in response.data
        assert response.data["error_code"] == ErrorCode.SERVICE_UNAVAILABLE.value


if __name__ == "__main__":
    pytest.main([__file__])