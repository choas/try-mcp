#!/usr/bin/env python3

import asyncio
import json
import sys
import logging
from typing import Dict, Any

import aiohttp

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def send_mcp_request(url: str, method: str, params: Dict[str, Any] = None, request_id: int = 1):
    """Send an MCP request to the server."""
    if params is None:
        params = {}
    
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    logger.info(f"Sending {method} request to {url}")
    logger.debug(f"Request payload: {json.dumps(payload)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Response: {json.dumps(result)}")
                    return result
                else:
                    logger.error(f"HTTP error: {response.status}")
                    logger.error(await response.text())
                    return None
    except Exception as e:
        logger.error(f"Request error: {e}")
        return None

async def debug_claude_request():
    """Debug the exact request Claude Desktop is sending."""
    server_url = "http://localhost:8003/mcp"
    
    # Exact Claude Desktop request
    payload = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "prompts/list",
        "params": {}
    }
    
    logger.info("=== Testing Claude Desktop Request ===")
    logger.info(f"Request: {json.dumps(payload)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(server_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response: {json.dumps(result, indent=2)}")
                    
                    # Check if the response is valid
                    if "result" in result and "prompts" in result["result"]:
                        prompts = result["result"]["prompts"]
                        logger.info(f"✅ Success! Found {len(prompts)} prompts")
                        logger.info(f"First prompt: {prompts[0]['name']} - {prompts[0]['description']}")
                    elif "error" in result:
                        logger.error(f"❌ Error: {result['error']['message']}")
                    else:
                        logger.error("❓ Unknown response format")
                else:
                    logger.error(f"❌ HTTP Error: {response.status}")
                    logger.error(await response.text())
    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")
        logger.error("Note: This test requires the server to be running on port 8003.")

if __name__ == "__main__":
    try:
        import aiohttp
    except ImportError:
        logger.error("aiohttp not installed. Install with: pip install aiohttp")
        sys.exit(1)
    
    asyncio.run(debug_claude_request())