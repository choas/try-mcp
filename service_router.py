"""Service router for the multi-service MCP platform."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from data.models import ServiceRequest, ServiceResponse, ServiceInfo
from services.base_service import BaseService
from utils.error_formatter import ErrorFormatter, ErrorCode, ErrorHandler

logger = logging.getLogger(__name__)


class ServiceRouter:
    """Routes requests to appropriate services based on URL patterns."""
    
    def __init__(self):
        """Initialize the service router."""
        self._services: Dict[str, Dict[str, BaseService]] = {}
        self._url_pattern = re.compile(r'^/([^/]+)/v(\d+)(?:/.*)?$')
    
    def register_service(self, service: BaseService) -> None:
        """Register a service with the router.
        
        Args:
            service: Service instance to register
        """
        service_name = service.name.lower()
        if service_name not in self._services:
            self._services[service_name] = {}
        
        self._services[service_name][service.version] = service
    
    def unregister_service(self, service_name: str, version: str) -> bool:
        """Unregister a service from the router.
        
        Args:
            service_name: Name of the service to unregister
            version: Version of the service to unregister
            
        Returns:
            True if service was unregistered, False if not found
        """
        service_name = service_name.lower()
        if service_name in self._services and version in self._services[service_name]:
            del self._services[service_name][version]
            if not self._services[service_name]:
                del self._services[service_name]
            return True
        return False
    
    def parse_url(self, url: str) -> Optional[Tuple[str, str]]:
        """Parse URL to extract service name and version.
        
        Args:
            url: URL to parse (e.g., "/weather/v1" or "http://domain/weather/v1")
            
        Returns:
            Tuple of (service_name, version) or None if invalid
        """
        # Handle full URLs by extracting the path
        if url.startswith(('http://', 'https://')):
            parsed = urlparse(url)
            path = parsed.path
        else:
            path = url
        
        # Reject paths that don't start with slash as invalid
        if not path.startswith('/'):
            return None
        
        match = self._url_pattern.match(path)
        if match:
            service_name = match.group(1).lower()
            version = f"v{match.group(2)}"
            return service_name, version
        
        return None
    
    def get_service(self, service_name: str, version: str) -> Optional[BaseService]:
        """Get a registered service by name and version.
        
        Args:
            service_name: Name of the service
            version: Version of the service
            
        Returns:
            Service instance or None if not found
        """
        service_name = service_name.lower()
        return self._services.get(service_name, {}).get(version)
    
    def list_services(self) -> List[ServiceInfo]:
        """List all registered services.
        
        Returns:
            List of ServiceInfo objects for all registered services
        """
        services = []
        for service_name, versions in self._services.items():
            for version, service in versions.items():
                services.append(service.get_service_info())
        return services
    
    def get_available_services(self) -> List[str]:
        """Get list of available service names.
        
        Returns:
            List of service names
        """
        return list(self._services.keys())
    
    def get_service_versions(self, service_name: str) -> List[str]:
        """Get available versions for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of available versions
        """
        service_name = service_name.lower()
        return list(self._services.get(service_name, {}).keys())
    
    async def route_request(self, url: str, method: str, params: Dict, request_id: str) -> ServiceResponse:
        """Route a request to the appropriate service.
        
        Args:
            url: Request URL
            method: MCP method name
            params: Request parameters
            request_id: Unique request identifier
            
        Returns:
            ServiceResponse with result or error
        """
        logger.info(f"ROUTE_REQUEST - URL: {url}, Method: {method}, RequestID: {request_id}")
        
        # Parse the URL
        parsed = self.parse_url(url)
        if not parsed:
            error_response = ErrorFormatter.format_error(
                code=ErrorCode.INVALID_URL_FORMAT,
                message="Invalid URL format. Expected: /<service>/v<version>",
                data={"available_services": self.get_available_services()},
                request_id=request_id
            )
            
            ErrorHandler.log_error(
                error_type="ROUTING_ERROR",
                message=f"Invalid URL format: {url}",
                context={"url": url, "request_id": request_id}
            )
            
            return ServiceResponse(
                success=False,
                error="Invalid URL format. Expected: /<service>/v<version>",
                data={"available_services": self.get_available_services(), "error_code": ErrorCode.INVALID_URL_FORMAT.value}
            )
        
        service_name, version = parsed
        logger.debug(f"Parsed URL: service={service_name}, version={version}")
        
        # Find the service
        service = self.get_service(service_name, version)
        if not service:
            available_versions = self.get_service_versions(service_name)
            
            if available_versions:
                # Service exists but version not found
                error_code = ErrorCode.VERSION_NOT_SUPPORTED
                error_msg = f"Service '{service_name}' version '{version}' not found. Available versions: {available_versions}"
                
                ErrorHandler.log_error(
                    error_type="VERSION_ERROR",
                    message=error_msg,
                    context={
                        "service": service_name,
                        "version": version,
                        "available_versions": available_versions,
                        "request_id": request_id
                    }
                )
            else:
                # Service not found
                error_code = ErrorCode.SERVICE_NOT_FOUND
                error_msg = f"Service '{service_name}' not found. Available services: {self.get_available_services()}"
                
                ErrorHandler.log_error(
                    error_type="SERVICE_ERROR",
                    message=error_msg,
                    context={
                        "service": service_name,
                        "available_services": self.get_available_services(),
                        "request_id": request_id
                    }
                )
            
            return ServiceResponse(
                success=False,
                error=error_msg,
                data={
                    "service": service_name,
                    "version": version,
                    "available_services": self.get_available_services(),
                    "error_code": error_code.value
                }
            )
        
        # Check service status
        if service.get_status() != "active":
            error_msg = f"Service '{service_name}' is currently {service.get_status()}"
            
            ErrorHandler.log_error(
                error_type="SERVICE_STATUS_ERROR",
                message=error_msg,
                context={
                    "service": service_name,
                    "status": service.get_status(),
                    "request_id": request_id
                }
            )
            
            return ServiceResponse(
                success=False,
                error=error_msg,
                data={
                    "service": service_name,
                    "status": service.get_status(),
                    "error_code": ErrorCode.SERVICE_UNAVAILABLE.value
                }
            )
        
        try:
            # Log the request
            logger.info(f"SERVICE_REQUEST - Service: {service_name}, Version: {version}, Method: {method}")
            
            # Route to the service
            result = await service.handle_request(method, params)
            
            # Log the response
            is_error = result.is_error
            log_level = logging.WARNING if is_error else logging.INFO
            logger.log(
                log_level,
                f"SERVICE_RESPONSE - Service: {service_name}, Success: {not is_error}",
                extra={
                    "service": service_name,
                    "version": version,
                    "method": method,
                    "is_error": is_error,
                    "request_id": request_id
                }
            )
            
            return ServiceResponse(
                success=True,
                data={
                    "service": service_name,
                    "version": version,
                    "result": {
                        "content": result.content,
                        "is_error": result.is_error
                    }
                }
            )
            
        except Exception as e:
            # Handle and log the exception
            error_response, log_data = ErrorHandler.handle_exception(
                exception=e,
                error_type="SERVICE_EXECUTION_ERROR",
                context={
                    "service": service_name,
                    "version": version,
                    "method": method,
                    "request_id": request_id
                },
                request_id=request_id
            )
            
            return ServiceResponse(
                success=False,
                error=f"Service error: {str(e)}",
                data={
                    "service": service_name,
                    "version": version,
                    "method": method,
                    "error_code": ErrorCode.SERVICE_ERROR.value,
                    "error_type": "SERVICE_EXECUTION_ERROR"
                }
            )
    
    def validate_url_pattern(self, url: str) -> bool:
        """Validate if URL matches the expected pattern.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL matches pattern, False otherwise
        """
        return self.parse_url(url) is not None
    
    def get_service_count(self) -> int:
        """Get total number of registered services.
        
        Returns:
            Total number of service instances
        """
        count = 0
        for versions in self._services.values():
            count += len(versions)
        return count