"""Base service interface for the multi-service MCP platform."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from data.models import ServiceInfo, ToolDefinition, ToolResult


class BaseService(ABC):
    """Abstract base class for all MCP services."""
    
    def __init__(self, name: str, version: str, description: str):
        """Initialize the base service.
        
        Args:
            name: Service name
            version: Service version
            description: Service description
        """
        self.name = name
        self.version = version
        self.description = description
        self._tools: List[ToolDefinition] = []
        self._status = "active"
    
    @abstractmethod
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        pass
    
    def get_service_info(self) -> ServiceInfo:
        """Get service information.
        
        Returns:
            ServiceInfo object with service details
        """
        return ServiceInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            tools=self.get_tools(),
            status=self._status
        )
    
    def set_status(self, status: str) -> None:
        """Set the service status.
        
        Args:
            status: New status (active, inactive, error)
        """
        self._status = status
    
    def get_status(self) -> str:
        """Get the current service status.
        
        Returns:
            Current service status
        """
        return self._status
    
    def add_tool(self, tool: ToolDefinition) -> None:
        """Add a tool definition to this service.
        
        Args:
            tool: Tool definition to add
        """
        self._tools.append(tool)
    
    def _create_text_response(self, text: str, is_error: bool = False) -> ToolResult:
        """Create a text response.
        
        Args:
            text: Response text
            is_error: Whether this is an error response
            
        Returns:
            ToolResult with text content
        """
        return ToolResult(
            content=[{
                "type": "text",
                "text": text
            }],
            is_error=is_error
        )
    
    def _create_error_response(self, error_message: str) -> ToolResult:
        """Create an error response.
        
        Args:
            error_message: Error message
            
        Returns:
            ToolResult with error content
        """
        return self._create_text_response(f"Error: {error_message}", is_error=True)
    
    def supports_prompts(self) -> bool:
        """Check if this service supports MCP prompts.
        
        Returns:
            True if service supports prompts, False otherwise
        """
        return False
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get MCP prompts provided by this service.
        
        Returns:
            List of prompt definitions in MCP format
        """
        return []