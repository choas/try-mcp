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

**For HTTP MCP Server:**
```json
{
  "mcpServers": {
    "mvg-mcp-http": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://your-server:8000/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

Replace `your-server` with your actual server hostname or IP address.

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

Both tests will verify that all MCP functionality is working correctly with real Munich transport data.

## Usage with Claude Desktop

Once configured, you can ask Claude things like:
- "Check departures from Hauptbahnhof"
- "What trains are leaving from Marienplatz?"
- "Show me departures from Sendlinger Tor in 10 minutes"
- "Find the station ID for Odeonsplatz"

The service will provide real-time departure information with clean, formatted output including emojis and departure details.
