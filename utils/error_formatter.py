"""
Error handling and response formatting utilities for the multi-service MCP platform.

This module provides standardized error codes, error response formatting,
and error handling utilities for consistent error handling across the platform.
"""

import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the multi-service MCP platform."""
    
    # JSON-RPC standard error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom error codes for the platform
    SERVICE_NOT_FOUND = -33000
    VERSION_NOT_SUPPORTED = -33001
    SERVICE_UNAVAILABLE = -33002
    INVALID_URL_FORMAT = -33003
    TOOL_NOT_FOUND = -33004
    PARAMETER_VALIDATION_ERROR = -33005
    RATE_LIMIT_EXCEEDED = -33006
    AUTHORIZATION_ERROR = -33007
    
    # Service-specific error codes (range -34000 to -34999)
    SERVICE_ERROR = -34000


class ErrorFormatter:
    """Utility class for formatting error responses."""
    
    @staticmethod
    def format_error(
        code: Union[ErrorCode, int],
        message: str,
        data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """Format an error response according to the JSON-RPC 2.0 specification.
        
        Args:
            code: Error code (from ErrorCode enum or custom integer)
            message: Error message
            data: Additional error data (optional)
            request_id: Request ID (optional)
            include_traceback: Whether to include traceback in the response (default: False)
            
        Returns:
            Formatted error response
        """
        # Convert ErrorCode enum to integer if needed
        if isinstance(code, ErrorCode):
            code_value = code.value
        else:
            code_value = code
        
        # Create error object
        error_obj = {
            "code": code_value,
            "message": message
        }
        
        # Add data if provided
        if data is not None:
            error_obj["data"] = data
        
        # Add traceback if requested (for development/debugging only)
        if include_traceback:
            error_obj["traceback"] = traceback.format_exc()
        
        # Create full response
        response = {
            "jsonrpc": "2.0",
            "error": error_obj
        }
        
        # Add request ID if provided
        if request_id is not None:
            response["id"] = request_id
        
        return response
    
    @staticmethod
    def service_not_found_error(
        service_name: str,
        available_services: list,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a service not found error response.
        
        Args:
            service_name: Name of the service that was not found
            available_services: List of available services
            request_id: Request ID (optional)
            
        Returns:
            Formatted error response
        """
        return ErrorFormatter.format_error(
            code=ErrorCode.SERVICE_NOT_FOUND,
            message=f"Service '{service_name}' not found",
            data={
                "service": service_name,
                "available_services": available_services
            },
            request_id=request_id
        )
    
    @staticmethod
    def version_not_supported_error(
        service_name: str,
        version: str,
        available_versions: list,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a version not supported error response.
        
        Args:
            service_name: Name of the service
            version: Version that was not supported
            available_versions: List of available versions
            request_id: Request ID (optional)
            
        Returns:
            Formatted error response
        """
        return ErrorFormatter.format_error(
            code=ErrorCode.VERSION_NOT_SUPPORTED,
            message=f"Service '{service_name}' version '{version}' not supported",
            data={
                "service": service_name,
                "version": version,
                "available_versions": available_versions
            },
            request_id=request_id
        )
    
    @staticmethod
    def method_not_found_error(
        method: str,
        available_methods: Optional[list] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a method not found error response.
        
        Args:
            method: Name of the method that was not found
            available_methods: List of available methods (optional)
            request_id: Request ID (optional)
            
        Returns:
            Formatted error response
        """
        data = {"method": method}
        if available_methods is not None:
            data["available_methods"] = available_methods
        
        return ErrorFormatter.format_error(
            code=ErrorCode.METHOD_NOT_FOUND,
            message=f"Method '{method}' not found",
            data=data,
            request_id=request_id
        )
    
    @staticmethod
    def invalid_params_error(
        message: str,
        param_name: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format an invalid parameters error response.
        
        Args:
            message: Error message
            param_name: Name of the invalid parameter (optional)
            request_id: Request ID (optional)
            
        Returns:
            Formatted error response
        """
        data = {}
        if param_name is not None:
            data["param"] = param_name
        
        return ErrorFormatter.format_error(
            code=ErrorCode.INVALID_PARAMS,
            message=message,
            data=data,
            request_id=request_id
        )
    
    @staticmethod
    def service_unavailable_error(
        service_name: str,
        status: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a service unavailable error response.
        
        Args:
            service_name: Name of the service
            status: Current status of the service
            request_id: Request ID (optional)
            
        Returns:
            Formatted error response
        """
        return ErrorFormatter.format_error(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"Service '{service_name}' is currently {status}",
            data={
                "service": service_name,
                "status": status
            },
            request_id=request_id
        )
    
    @staticmethod
    def internal_error(
        message: str,
        request_id: Optional[str] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """Format an internal error response.
        
        Args:
            message: Error message
            request_id: Request ID (optional)
            include_traceback: Whether to include traceback (default: False)
            
        Returns:
            Formatted error response
        """
        return ErrorFormatter.format_error(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            request_id=request_id,
            include_traceback=include_traceback
        )


class ErrorHandler:
    """Error handling utilities for the multi-service MCP platform."""
    
    @staticmethod
    def log_error(
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log an error with standardized format.
        
        Args:
            error_type: Type of error (e.g., "SERVICE_ERROR", "ROUTING_ERROR")
            message: Error message
            context: Additional context information (optional)
            exc_info: Whether to include exception info in the log (default: False)
        """
        log_data = {
            "error_type": error_type,
            "error_message": message  # Changed from 'message' to 'error_message'
        }
        
        if context is not None:
            log_data["context"] = context
        
        logger.error(f"ERROR - {error_type}: {message}", extra=log_data, exc_info=exc_info)
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        error_type: str,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Handle an exception and return a formatted error response.
        
        Args:
            exception: The exception to handle
            error_type: Type of error (e.g., "SERVICE_ERROR", "ROUTING_ERROR")
            context: Additional context information (optional)
            request_id: Request ID (optional)
            
        Returns:
            Tuple of (error_response, log_data)
        """
        message = str(exception)
        
        # Log the error
        log_data = {
            "error_type": error_type,
            "error_message": message,  # Changed from 'message' to 'error_message'
            "exception": type(exception).__name__
        }
        
        if context is not None:
            log_data["context"] = context
        
        logger.error(
            f"EXCEPTION - {error_type}: {message} ({type(exception).__name__})",
            extra=log_data,
            exc_info=True
        )
        
        # Create error response
        error_response = ErrorFormatter.format_error(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Internal error: {message}",
            request_id=request_id
        )
        
        return error_response, log_data