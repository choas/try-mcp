# MVG MCP

This project provides both a command-line interface and an MCP (Model Context Protocol) service to find public transport departures in Munich, Germany using the MVG API.

## Features

- **Command-line interface** - Get departures directly from the terminal
- **MCP service** - Integrate with AI assistants like Claude Desktop
- **Real-time data** - Live departure information from Munich's public transport system
- **Station lookup** - Find stations by name
- **Time offset support** - Check departures at future times
- **Error handling** - Graceful handling of invalid stations or API issues

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


## Running the Application

### Command Line Interface

You can run the CLI application with:

```bash
python main.py <station_name> [--offset <minutes>]
```

Examples:
```bash
# Get departures from Hauptbahnhof now
python main.py Hauptbahnhof

# Get departures from Marienplatz in 10 minutes
python main.py Marienplatz --offset 10
```

### MCP Service

The project provides two MCP server options:

#### Option 1: Stdio MCP Server (for local use with Claude Desktop)

```bash
python mcp_server.py
```

#### Option 2: HTTP MCP Server (for remote hosting)

```bash
python mcp_http_server.py
```

This starts an HTTP server on `http://localhost:8000` with:
- `/mcp` - MCP protocol endpoint (POST)
- `/health` - Health check endpoint (GET)
- `/` - Service information (GET)

#### Option 3: SSE MCP Server (streamable HTTP with Server-Sent Events)

```bash
python mcp_sse_server.py
```

This starts an SSE-enabled server on `http://localhost:8001` with:
- `/mcp` - Standard MCP protocol endpoint (POST)
- `/mcp/stream` - SSE streaming endpoint (GET)
- `/mcp/stream/{connection_id}` - Send to specific stream (POST)
- `/health` - Health check with connection count (GET)
- `/` - Service information with capabilities (GET)

**Features:**
- ✅ **Streamable transport** - Future-ready for MCP evolution
- ✅ **Server-Sent Events** - Real-time bidirectional communication
- ✅ **CORS support** - Web client compatibility
- ✅ **Connection management** - Multiple concurrent connections
- ✅ **Keepalive** - Automatic connection maintenance

Both MCP services provide the same two tools:
- `get_departures`: Get public transport departures from a station
- `find_station`: Find a station ID by name

#### Claude Desktop App Configuration

Add this to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

**Using uv (recommended):**
```json
{
  "mcpServers": {
    "mvg-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/mvg-mcp-project",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
```

**Alternative direct Python approach:**
```json
{
  "mcpServers": {
    "mvg-mcp": {
      "command": "python",
      "args": ["/path/to/your/mvg-mcp-project/mcp_server.py"],
      "cwd": "/path/to/your/mvg-mcp-project",
      "env": {
        "PATH": "/path/to/your/mvg-mcp-project/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

Replace `/path/to/your/mvg-mcp-project` with the actual path to your project directory.

**For Remote HTTP MCP Server (via Bridge):**

If you want to connect to a remote HTTP MCP server, use the bridge:

```json
{
  "mcpServers": {
    "mvg-mcp-remote": {
      "command": "python",
      "args": ["/path/to/your/mvg-mcp-project/mcp_bridge.py", "--url", "http://your-server:8000"],
      "cwd": "/path/to/your/mvg-mcp-project"
    }
  }
}
```

Replace `your-server` with your actual server hostname or IP address.

> **Note**: Claude Desktop currently focuses on stdio-based MCP servers. HTTP support is limited, with future plans for Streamable HTTP and SSE protocols. The HTTP server is useful for other integrations and Claude Code has better remote MCP support.

## Testing

**Test the stdio MCP server locally:**
```bash
python test_mcp.py
```

**Test the HTTP MCP server:**
```bash
# First, start the HTTP server in one terminal:
python mcp_http_server.py

# Then in another terminal, run the test:
python test_http_mcp.py
```

**Test the SSE MCP server:**
```bash
# First, start the SSE server in one terminal:
python mcp_sse_server.py

# Then in another terminal, run the test:
python test_sse_mcp.py

# For interactive SSE testing (keeps connection open):
python test_sse_mcp.py --interactive
```

All tests will verify that MCP functionality is working correctly with real Munich transport data.

## Usage with Claude Desktop

Once configured, you can ask Claude things like:
- "Check departures from Hauptbahnhof"
- "What trains are leaving from Marienplatz?"
- "Show me departures from Sendlinger Tor in 10 minutes"
- "Find the station ID for Odeonsplatz"

The service will provide real-time departure information with clean, formatted output including emojis and departure details.
