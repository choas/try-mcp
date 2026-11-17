# Multi-Service MCP Platform

A comprehensive Model Context Protocol (MCP) platform that hosts multiple utility services through a unified HTTP-based API structure. The platform provides various services including mindful sentences, weather forecasts, emoji oracle, random timestamps, fortune cookies, and lucky numbers.

## Features

### Platform Features

- **Unified API Structure**: Access all services through a consistent URL pattern: `http(s)://<domain>/<service>/<version>`
- **Service Registry**: Dynamic service discovery and management
- **Service Router**: Intelligent request routing to appropriate service handlers
- **MCP Protocol Support**: Full implementation of MCP protocol methods
- **Error Handling**: Comprehensive error handling with structured error codes
- **Configuration Management**: Enable/disable services through configuration
- **Health Monitoring**: Service status reporting and health checks
- **CORS Support**: Cross-origin resource sharing for web clients
- **Landing Page**: User-friendly documentation and service showcase

### Available Services

1. **Mindful Service** (`/mindful/v1`): Daily inspirational mindful sentences with rotation
2. **Weather Service** (`/weather/v1`): Optimistic weather forecasts with pleasant conditions
3. **Emoji Oracle Service** (`/emoji-oracle/v1`): Cryptic guidance through symbolic emoji combinations
4. **Timestamp Service** (`/timestamp/v1`): Random timestamp generation within specified ranges
5. **Fortune Cookie Service** (`/fortune/v1`): Surreal and cryptic fortune phrases that change hourly
6. **Lucky Numbers Service** (`/lucky-numbers/v1`): Mystical number generation for various life scenarios

## Prerequisites

- Python 3.11+
- FastAPI
- Uvicorn

## Setup

There are two ways to set up the environment: using `venv` or `uv`.

### Using `venv` (standard library)

1. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

2. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Using `uv`

1. **Initialize the project:**
   ```bash
   uv init
   ```
2. **Create a virtual environment:**
   ```bash
   uv venv
   ```
3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

## Running the Multi-Service Platform

Start the multi-service platform with:

```bash
python start_platform.py
```

This will display detailed information about available services and endpoints before starting the server.

This starts an HTTP server on `http://localhost:8003` with the following endpoints:

- `/mcp` - Main MCP protocol endpoint
- `/services/{service_name}/v{version}` - Service-specific MCP endpoints
- `/services/{service_name}/v{version}/{method}` - Direct service method calls
- `/services` - List all available services
- `/services/{service_name}` - Get information about a specific service
- `/health` - Health check endpoint
- `/` - Landing page with service information

## Service Architecture

The platform uses a plugin-based architecture with the following components:

- **ServiceRegistry**: Manages service discovery and instantiation
- **ServiceRouter**: Routes requests to appropriate services
- **BaseService**: Abstract base class for all services
- **Service Implementations**: Individual service classes

### Adding New Services

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
    
    def get_tools(self):
        return [{
            "name": "my_tool",
            "description": "My custom tool",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }]
    
    async def handle_request(self, method, params):
        if method == "my_tool":
            return self._create_text_response("Custom response")
        else:
            return self._create_error_response(f"Unknown method: {method}")
```

## Service Details

### Mindful Service

The Mindful Service provides inspirational sentences that rotate throughout the day.

#### Endpoints

- `/mindful/v1`

#### Tools

1. **get_mindful_sentence**
   - **Description**: Get an inspirational mindful sentence for the day
   - **Parameters**: None
   - **Example Response**:
     ```
     "Take a moment to breathe deeply and connect with the present moment."
     ```

#### Features

- Pool of 50+ inspirational sentences
- Daily rotation with 4 different sentences per day
- Consistent sentences within the same day

### Weather Service

The Weather Service provides consistently optimistic weather forecasts.

#### Endpoints

- `/weather/v1`

#### Tools

1. **get_weather_forecast**
   - **Description**: Get an optimistic weather forecast for tomorrow
   - **Parameters**: None
   - **Example Response**:
     ```
     "Tomorrow will be a beautiful day with a temperature of 22°C (72°F) and partly cloudy skies. Perfect for outdoor activities!"
     ```

#### Features

- Always predicts pleasant weather conditions
- Temperature ranges between 18-24°C (64-75°F)
- Only sunny or partly cloudy conditions
- No rain, storms, or extreme temperatures

### Emoji Oracle Service

The Emoji Oracle Service provides cryptic guidance through emoji combinations.

#### Endpoints

- `/emoji-oracle/v1`

#### Tools

1. **get_emoji_oracle**
   - **Description**: Get a cryptic three-emoji combination as guidance
   - **Parameters**: None
   - **Example Response**:
     ```
     "🌟 🔑 🚪"
     ```

#### Features

- Returns exactly 3 emojis per request
- Draws from a diverse pool of meaningful symbols
- Creates potentially interpretable but cryptic messages
- Different combinations for each request

### Timestamp Service

The Timestamp Service generates random timestamps within specified ranges.

#### Endpoints

- `/timestamp/v1`

#### Tools

1. **generate_random_timestamp**
   - **Description**: Generate a random timestamp within a specified range
   - **Parameters**:
     - `start_time` (string, optional): Start of the time range (ISO 8601 format)
     - `end_time` (string, optional): End of the time range (ISO 8601 format)
   - **Example**:
     ```json
     {
       "start_time": "2025-01-01T00:00:00Z",
       "end_time": "2025-12-31T23:59:59Z"
     }
     ```

#### Features

- Generates random timestamps within specified ranges
- Automatically swaps start/end times if start is after end
- Default range is next day between 10:00 and 16:00
- Returns timestamps in ISO 8601 format

### Fortune Cookie Service

The Fortune Cookie Service provides surreal and cryptic phrases that change hourly.

#### Endpoints

- `/fortune/v1`

#### Tools

1. **get_fortune_cookie**
   - **Description**: Get a surreal, cryptic fortune phrase
   - **Parameters**: None
   - **Example Response**:
     ```
     "The silent whisper of forgotten dreams echoes in the corridors of possibility."
     ```

#### Features

- Generates surreal, cryptic phrases
- Same phrase returned within the same hour
- New phrase generated each hour
- LLM integration for content generation
- Supports MCP prompts/list method

### Lucky Numbers Service

The Lucky Numbers Service generates "statistically blessed" numbers for various life scenarios.

#### Endpoints

- `/lucky-numbers/v1`

#### Tools

1. **generate_blessed_numbers**
   - **Description**: Generates mystically optimized numbers for various life scenarios
   - **Parameters**:
     - `scenario` (string, required): The scenario for which you need lucky numbers
       - Options: lottery, decision, restaurant, date, love, career, creativity, health, travel, learning
     - `count` (integer, optional): Number of lucky numbers to generate (1-10)
     - `min_value` (integer, optional): Minimum value for generated numbers
     - `max_value` (integer, optional): Maximum value for generated numbers
     - `energy_level` (string, optional): Intensity of cosmic energy applied
       - Options: low, medium, high, extreme
   - **Example**:
     ```json
     {
       "scenario": "lottery",
       "count": 6,
       "min_value": 1,
       "max_value": 49,
       "energy_level": "high"
     }
     ```

#### Features

- Scenario-specific number generation for 10 different contexts
- Mystical methodology explanations and cosmic alignment calculation
- Customizable parameters (count, range, energy level)
- Formatted responses with emojis and encouraging language

## MCP Protocol Support

The platform answers two protocol eras on the same endpoints:

- **Legacy (`2025-06-18`)**: the client opens with `initialize`.
- **Modern (`2026-07-28`, "MCP v2")**: stateless, no `initialize`. Every request carries the protocol version in `params._meta` and in the `MCP-Protocol-Version` header, plus the `Mcp-Method` header (and `Mcp-Name` for `tools/call`, `prompts/get` and `resources/read`).

| Endpoint | Eras |
|---|---|
| `/mcp` | both |
| `/services/<name>/v1` | both |
| `/services/<name>/v2` | only `2026-07-28`; `initialize` is rejected with `-32022` |

Supported methods:

- **initialize** (legacy only) and **server/discover** (modern only)
- **tools/list**, **tools/call**
- **prompts/list**, **prompts/get**
- **resources/list**, **resources/read** (modern also answers **resources/templates/list** with an empty list)

### Prompts and resources

| Service | Prompt | Resources |
|---|---|---|
| mindful | `mindful_pause` | `mindful://sentences` |
| weather | `plan_my_day` | `weather://conditions` |
| emoji-oracle | `ask_the_oracle` | `emoji-oracle://symbols` |
| timestamp | `surprise_schedule` | `timestamp://day-periods` |
| fortune | `fortune_prompt_1` to `fortune_prompt_30` | `fortune://generation-instructions`, `fortune://inspirations` |
| lucky-numbers | `blessed_numbers_reading` | `lucky-numbers://scenarios` |

The protocol handling lives in `mcp_protocol.py`, the tests in `tests/integration/test_mcp_v2.py`.

## Server Catalog Page

`static/index.html` (served at `/`) is a static catalog of MCP servers with a configuration builder for Claude Code, Claude Desktop, Codex, Antigravity, VS Code and the MCP Inspector. Values typed into the page stay in the browser. The example services page moved to `/examples/`.

The catalog data comes from the official MCP Registry and is embedded into the page at build time:

```bash
python3 tools/build_catalog.py fetch probe inject
```

- `fetch` reads the servers named in `tools/curated.json` from the registry (plus `tools/manual.json`).
- `probe` sends one unauthenticated `server/discover` request to each remote server and stores the result as the V2 flag.
- `inject` writes `tools/servers.json` into `static/index.html`.
- `verify` checks every entry (registry status, docs link, remote URL, npm or PyPI package) and writes `tools/verify_report.json`. It changes nothing.

Corrections for registry entries that are out of date go into `tools/overrides.json`.

## API Usage Examples

### Using the Main MCP Endpoint

```bash
# List all available tools
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}'

# Call a specific tool
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "mindful_get_mindful_sentence",
    "arguments": {}
  }
}'
```

### Using Service-Specific Endpoints

```bash
# List tools for a specific service
curl -X POST http://localhost:8003/services/lucky-numbers/v1 -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}'

# Call a specific tool on a service
curl -X POST http://localhost:8003/services/lucky-numbers/v1 -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "generate_blessed_numbers",
    "arguments": {
      "scenario": "lottery",
      "count": 6
    }
  }
}'
```

### Using Direct Method Calls

```bash
# Call a method directly
curl -X POST http://localhost:8003/services/weather/v1/get_weather_forecast -H "Content-Type: application/json" -d '{
  "location": "Berlin"
}'

# Get a mindful sentence
curl -X POST http://localhost:8003/services/mindful/v1/get_mindful_sentence
```

## Configuration

The platform can be configured using a JSON configuration file or environment variables.

### Configuration File (config.json)

```json
{
  "server": {
    "log_level": "info",
    "port": 8003
  },
  "services": {
    "mindful": {
      "enabled": true
    },
    "weather": {
      "enabled": true
    },
    "emoji-oracle": {
      "enabled": true
    },
    "timestamp": {
      "enabled": true
    },
    "fortune": {
      "enabled": true
    },
    "lucky-numbers": {
      "enabled": true
    }
  }
}
```

### Environment Variables

- `MCP_CONFIG`: Path to configuration file (default: `config.json`)
- `MCP_LOG_LEVEL`: Logging level (default: `info`)
- `MCP_PORT`: Server port (default: `8003`)
- `MCP_SERVICE_<NAME>_ENABLED`: Enable/disable specific services (e.g., `MCP_SERVICE_WEATHER_ENABLED=true`)

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

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/

# Run tests for specific services
python -m pytest tests/unit/services/test_lucky_numbers_service.py
python -m pytest tests/integration/test_mindful_service_integration.py
```

### Test Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for service interactions
- `tests/performance/`: Performance and concurrency tests

### MCP Test with Inspector

This command initiates a Model Context Protocol (MCP) test session using the Inspector tool to validate and debug contextual behavior.

```shell
npx @modelcontextprotocol/inspector
```

## Docker Support

The project includes a Dockerfile for containerization:

```bash
# Build the Docker image
docker build -t multi-service-mcp .

# Run the container
docker run -p 8003:8003 multi-service-mcp
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.