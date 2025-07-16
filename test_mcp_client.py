#!/usr/bin/env python3

import asyncio
import json
import sys
import logging
from typing import Dict, Any

import aiohttp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
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

async def test_mcp_server():
    """Test the MCP server with various requests."""
    server_url = "http://localhost:8003/mcp"
    
    # Test 1: Initialize
    logger.info("=== Test 1: Initialize ===")
    init_response = await send_mcp_request(server_url, "initialize")
    if init_response and "result" in init_response:
        logger.info("✅ Initialize successful")
        logger.info(f"Protocol version: {init_response['result'].get('protocolVersion')}")
        logger.info(f"Capabilities: {json.dumps(init_response['result'].get('capabilities'))}")
    else:
        logger.error("❌ Initialize failed")
    
    # Test 2: Tools List
    logger.info("\n=== Test 2: Tools List ===")
    tools_response = await send_mcp_request(server_url, "tools/list", request_id=2)
    if tools_response and "result" in tools_response and "tools" in tools_response["result"]:
        tools = tools_response["result"]["tools"]
        logger.info(f"✅ Tools list successful: {len(tools)} tools found")
        for i, tool in enumerate(tools[:3]):  # Show first 3 tools
            logger.info(f"Tool {i+1}: {tool['name']} - {tool['description']}")
        if len(tools) > 3:
            logger.info(f"... and {len(tools) - 3} more tools")
    else:
        logger.error("❌ Tools list failed")
    
    # Test 3: Prompts List
    logger.info("\n=== Test 3: Prompts List ===")
    prompts_response = await send_mcp_request(server_url, "prompts/list", request_id=12)
    if prompts_response and "result" in prompts_response and "prompts" in prompts_response["result"]:
        prompts = prompts_response["result"]["prompts"]
        logger.info(f"✅ Prompts list successful: {len(prompts)} prompts found")
        for i, prompt in enumerate(prompts[:3]):  # Show first 3 prompts
            logger.info(f"Prompt {i+1}: {prompt['name']} - {prompt['description']}")
        if len(prompts) > 3:
            logger.info(f"... and {len(prompts) - 3} more prompts")
    else:
        logger.error("❌ Prompts list failed")
        if "error" in prompts_response:
            logger.error(f"Error: {prompts_response['error']['message']}")
    
    # Test 4: Tool Call
    logger.info("\n=== Test 4: Tool Call ===")
    tool_response = await send_mcp_request(
        server_url, 
        "tools/call", 
        {"name": "fortune_get_fortune_cookie", "arguments": {}},
        request_id=4
    )
    if tool_response and "result" in tool_response:
        logger.info("✅ Tool call successful")
        if "content" in tool_response["result"]:
            content = tool_response["result"]["content"]
            if content and len(content) > 0 and "text" in content[0]:
                logger.info(f"Response: {content[0]['text'][:100]}...")
    else:
        logger.error("❌ Tool call failed")
        if "error" in tool_response:
            logger.error(f"Error: {tool_response['error']['message']}")

if __name__ == "__main__":
    try:
        import aiohttp
    except ImportError:
        logger.error("aiohttp not installed. Install with: pip install aiohttp")
        sys.exit(1)
    
    logger.info("Starting MCP client test...")
    asyncio.run(test_mcp_server())