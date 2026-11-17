"""Base service interface for the multi-service MCP platform."""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
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
        self._prompt_definitions: List[Dict[str, Any]] = []
        self._resource_definitions: List[Dict[str, Any]] = []
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
    
    # ---------- prompts ----------

    def add_prompt(self, name: str, description: str, render: Callable[[Dict[str, str]], str],
                   arguments: Optional[List[Dict[str, Any]]] = None) -> None:
        """Register an MCP prompt.

        Args:
            name: Prompt name, unique across the platform
            description: What the prompt is for
            render: Function that turns the prompt arguments into the message text
            arguments: MCP argument definitions (name, description, required)
        """
        self._prompt_definitions.append({
            "name": name,
            "description": description,
            "arguments": arguments or [],
            "render": render,
        })

    def supports_prompts(self) -> bool:
        """Check if this service supports MCP prompts."""
        return bool(self._prompt_definitions)

    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get MCP prompts provided by this service, in MCP format."""
        return [{k: v for k, v in p.items() if k != "render"} for p in self._prompt_definitions]

    def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Build the result of `prompts/get`.

        Returns:
            The prompt result (description and messages), or None if this
            service has no prompt with that name

        Raises:
            ValueError: If a required argument is missing
        """
        arguments = {k: str(v) for k, v in (arguments or {}).items() if v is not None and str(v) != ""}
        for prompt in self._prompt_definitions:
            if prompt["name"] != name:
                continue
            missing = [a["name"] for a in prompt["arguments"] if a.get("required") and a["name"] not in arguments]
            if missing:
                raise ValueError(f"Missing required argument(s) for prompt '{name}': {', '.join(missing)}")
            return self._prompt_result(prompt["description"], prompt["render"](arguments))
        return None

    @staticmethod
    def _prompt_result(description: str, text: str) -> Dict[str, Any]:
        """Wrap a prompt text as one user message."""
        return {
            "description": description,
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }

    # ---------- resources ----------

    def add_resource(self, uri: str, name: str, description: str, read: Callable[[], Any],
                     mime_type: str = "application/json") -> None:
        """Register an MCP resource.

        Args:
            uri: Resource URI, unique across the platform
            name: Short name
            description: What the resource contains
            read: Function that returns the content. Text is sent as is,
                anything else is sent as JSON.
            mime_type: MIME type of the content
        """
        self._resource_definitions.append({
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
            "read": read,
        })

    def supports_resources(self) -> bool:
        """Check if this service supports MCP resources."""
        return bool(self._resource_definitions)

    def get_resources(self) -> List[Dict[str, Any]]:
        """Get MCP resources provided by this service, in MCP format."""
        return [{k: v for k, v in r.items() if k != "read"} for r in self._resource_definitions]

    def read_resource(self, uri: str) -> Optional[List[Dict[str, Any]]]:
        """Build the `contents` of `resources/read`, or None for an unknown URI."""
        for resource in self._resource_definitions:
            if resource["uri"] == uri:
                content = resource["read"]()
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False, indent=2)
                return [{"uri": uri, "mimeType": resource["mimeType"], "text": content}]
        return None
