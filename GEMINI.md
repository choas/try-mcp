# MVG MCP

## MCP Service

A simple MCP service to find departures in Munich, Germany.

### Features

- Takes a starting station as a command-line argument.
- Optionally takes a time offset in minutes from now (`--offset`).
- Returns a list of upcoming departures with their times, lines, and destinations.

### Usage

```bash
# Get departures from Hauptbahnhof now
python main.py Hauptbahnhof

# Get departures from Marienplatz in 10 minutes
python main.py Marienplatz --offset 10
```
