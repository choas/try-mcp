"""Data models for the multi-service MCP platform."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ServiceRequest:
    """Model for service requests."""
    service: str
    version: str
    method: str
    params: Dict[str, Any]
    request_id: str


@dataclass
class ServiceResponse:
    """Model for service responses."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ServiceInfo:
    """Model for service registration information."""
    name: str
    version: str
    description: str
    tools: List[Dict[str, Any]]
    status: str = "active"


@dataclass
class ToolDefinition:
    """Model for MCP tool definitions."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ToolResult:
    """Model for tool execution results."""
    content: List[Dict[str, Any]]
    is_error: bool = False