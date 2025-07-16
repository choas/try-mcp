# Multi-Service MCP Platform

This project provides a flexible, plugin-based MCP (Model Context Protocol) platform that hosts multiple services including:

- **MVG Service**: Munich public transport departures and station information
- **Mindful Service**: Daily inspirational mindful sentences
- **Emoji Oracle Service**: Cryptic guidance through symbolic emoji combinations
- **Fortune Cookie Service**: Surreal and cryptic fortune phrases that change hourly

## Features

### Platform Features
- **Plugin-based Architecture**: Easily add new services without modifying core code
- **Service Registry**: Dynamic service discovery and management
- **Generic MCP Implementation**: Supports all MCP methods across services
- **Service-specific Endpoints**: Individual MCP endpoints for each service
- **Prompts Support**: Full MCP prompts/list implementation
- **Error Handling**: Graceful handling of invalid requests or service issues

### Service Features
- **MVG Service**: Real-time departure information from Munich's public transport system
- **Mindful Service**: Daily rotation of inspirational sentences (4 per day)
- **Emoji Oracle Service**: Symbolic guidance through emoji combinations
- **Fortune Cookie Service**: Hourly-changing surreal fortune phrases with prompts support

## Prerequisites

- Python 3.11+

## Setup

There are two ways to set up the environment: using `venv` or `uv`.

### Using `venv` (standard library)

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Using `uv`

1.  **Initialize the project:**
    ```bash
    uv init
    ```
2.  **Create a virtual environment:**
    ```bash
    uv venv
    ```
3.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
4.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

## Running the Multi-Service Platform

Start the multi-service platform with:

```bash
python multi_service_server.py
```

This starts an HTTP server on `http://localhost:8003` with:
- `/mcp` - Main MCP protocol endpoint
- `/services/{service_name}/v{version}` - Service-specific MCP endpoints
- `/services/{service_name}/v{version}/{method}` - Direct service method calls
- `/services` - List all available services
- `/services/{service_name}` - Get information about a specific service
- `/health` - Health check endpoint
- `/` - Service information

## Running Individual Services

You can also run individual services directly:

### MVG Service

```bash
python mcp_server.py  # Stdio MCP Server
python mcp_streamable_server.py  # Streamable MCP Server (http://localhost:8002)
```

## Service Architecture

The platform uses a plugin-based architecture with the following components:

- **ServiceRegistry**: Manages service discovery and instantiation
- **ServiceRouter**: Routes requests to appropriate services
- **BaseService**: Abstract base class for all services
- **Service Implementations**: Individual service classes (MVG, Mindful, Emoji Oracle, Fortune)

Services can be added dynamically without modifying the core platform code:

```python
# Register a new service
registry = ServiceRegistry()
registry.register_service_class(MyCustomService)
server = MultiServiceMCPServer(service_registry=registry)
```

## MCP Protocol Support

The platform supports the following MCP methods:

- **initialize**: Initialize the MCP connection
- **tools/list**: List available tools across all services
- **tools/call**: Call a specific tool
- **prompts/list**: List available prompts (from services that support prompts)

Each service-specific endpoint also supports these methods for that particular service.

## Claude Desktop Configuration

Add this to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "multi-service-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/multi-service-mcp-project",
        "python",
        "multi_service_server.py"
      ]
    }
  }
}
```

Replace `/path/to/your/multi-service-mcp-project` with the actual path to your project directory.

## Testing

### Testing the Multi-Service Platform

```bash
# Run all tests
python -m pytest

# Test specific services
python -m pytest test_fortune_service.py
python -m pytest test_mvg_service.py
python -m pytest test_mindful_service.py
python -m pytest test_emoji_oracle_service.py

# Test service registry
python -m pytest test_service_registry.py

# Test MCP prompts integration
python -m pytest test_mcp_prompts_integration.py
```

### Testing Individual Endpoints

```bash
# Test the main MCP endpoint
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Test service-specific endpoints
curl -X POST http://localhost:8003/services/fortune/v1 -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"prompts/list","params":{}}'

# Test direct method calls
curl -X POST http://localhost:8003/services/mvg/v1/get_departures -H "Content-Type: application/json" -d '{"station":"Hauptbahnhof"}'
```

## Usage with Claude Desktop

Once configured, you can ask Claude to use various services:

### MVG Service
- "Check departures from Hauptbahnhof"
- "What trains are leaving from Marienplatz?"
- "Show me departures from Sendlinger Tor in 10 minutes"

### Mindful Service
- "Show me a mindful sentence for today"
- "I need some inspiration"

### Emoji Oracle Service
- "What does the emoji oracle say about my day?"
- "Give me an emoji reading"

### Fortune Cookie Service
- "What's my fortune today?"
- "Give me a fortune cookie"
- "Show me a cryptic fortune"

## Docker Support

The project includes a Dockerfile for containerization:

```bash
# Build the Docker image
docker build -t multi-service-mcp .

# Run the container
docker run -p 8003:8003 multi-service-mcp
```

## Extending with New Services

To add a new service:

1. Create a new service class that inherits from `BaseService`
2. Implement the required methods (`handle_request`, `get_tools`)
3. Optionally implement prompts support (`supports_prompts`, `get_prompts`)
4. Place the service in the `services/` directory
5. The service will be auto-discovered by the platform

Example:

```python
from services.base_service import BaseService
from data.models import ToolResult

class MyCustomService(BaseService):
    def __init__(self):
        super().__init__(
            name="custom",
            version="v1",
            description="My custom service"
        )
        self._tool_definitions = [
            {
                "name": "my_tool",
                "description": "My custom tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def handle_request(self, method, params):
        if method == "my_tool":
            return self._create_text_response("Custom response")
        else:
            return self._create_error_response(f"Unknown method: {method}")
    
    def get_tools(self):
        return self._tool_definitions.copy()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.