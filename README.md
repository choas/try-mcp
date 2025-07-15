# MVG MCP

This project provides both a command-line interface and an MCP (Model Context Protocol) service to find public transport departures in Munich, Germany using the MVG API.

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

### FastAPI Web Service

To run the web API:

```bash
uvicorn api:app --reload
```

Then visit `http://localhost:8000/docs` for the API documentation.


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
