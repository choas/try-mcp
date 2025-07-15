# server.py
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp = FastMCP("DateTime Server")

# Register a tool that returns the current date and time
@mcp.tool()
def current_datetime() -> str:
    """
    Return the current UTC date and time in ISO format.
    """
    return datetime.utcnow().isoformat() + "Z"

if __name__ == "__main__":
    mcp.run()

