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

To run as an MCP service:

```bash
python mcp_server.py
```

The MCP service provides two tools:
- `get_departures`: Get public transport departures from a station
- `find_station`: Find a station ID by name

#### Claude Desktop App Configuration

```json
{
  "mcpServers": {
    "mvg-mcp": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--directory",
        "/Users/lars/prj/mvg_mcp_C",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
```

Alternative direct Python approach:
```json
{
  "mcpServers": {
    "mvg-mcp": {
      "command": "python",
      "args": ["/Users/lars/prj/mvg_mcp_C/mcp_server.py"],
      "cwd": "/Users/lars/prj/mvg_mcp_C",
      "env": {
        "PATH": "/Users/lars/prj/mvg_mcp_C/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```



## Testing

To test the MCP server locally:

```bash
python test_mcp.py
```

This will verify that all MCP functionality is working correctly with real Munich transport data.

## Success! 🎉

Your MVG MCP service is now fully functional and can be used with Claude Desktop to get real-time Munich public transport information. The service provides:

- **Real-time departures** from any Munich station
- **Station lookup** by name
- **Clean, formatted output** with emojis and departure details
- **Error handling** for invalid stations or API issues

Simply ask Claude things like:
- "Check departures from Hauptbahnhof"
- "What trains are leaving from Marienplatz?"
- "Show me departures from Sendlinger Tor in 10 minutes"


## Running in a Sandbox (Docker file)

Connect to the container with:

```shell
podman exec -u 0 -it <container_name> /bin/bash
```

Install all necessary packages:

```shell
apt update
apt -y install python3 python3-pip python3-venv build-essential
```
