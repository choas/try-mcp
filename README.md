# MVG MCP

This project provides a simple command-line interface to find public transport connections in Munich, Germany using the MVG API.

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

Once the setup is complete, you can run the application with the following command:

```bash
python main.py
```

This will fetch and display the next departures from "Hauptbahnhof" to "Marienplatz".


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
