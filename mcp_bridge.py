#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPBridge:
    """Bridge between stdio MCP client and HTTP MCP server."""
    
    def __init__(self, http_server_url: str):
        self.http_server_url = http_server_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Start the bridge."""
        self.session = aiohttp.ClientSession()
        logger.info(f"Starting MCP Bridge to {self.http_server_url}")
    
    async def stop(self):
        """Stop the bridge."""
        if self.session:
            await self.session.close()
    
    async def forward_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Forward MCP request to HTTP server."""
        try:
            async with self.session.post(
                f"{self.http_server_url}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:  # No content for notifications
                    return None
                elif response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"HTTP server returned status {response.status}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"HTTP server error: {response.status}"
                        }
                    }
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Bridge error: {str(e)}"
                }
            }
    
    async def run(self):
        """Run the bridge stdio loop."""
        await self.start()
        
        try:
            while True:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue
                
                # Forward to HTTP server
                response = await self.forward_request(request)
                
                # Send response (if any)
                if response is not None:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
        
        finally:
            await self.stop()

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Bridge: stdio to HTTP")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="HTTP MCP server URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    bridge = MCPBridge(args.url)
    await bridge.run()

if __name__ == "__main__":
    asyncio.run(main())