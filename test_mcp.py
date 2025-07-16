#!/usr/bin/env python3

import asyncio
import json
from mcp_server import MVGMCPServer

async def test_mvg_mcp():
    """Test the MVG MCP server."""
    print("Testing MVG MCP Server...")
    
    server = MVGMCPServer()
    
    # Test initialize
    print("\n1. Testing initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    response = await server.handle_request(init_request)
    if response and response.get("result"):
        print("✅ Initialize successful")
        print(f"   Server: {response['result']['serverInfo']['name']}")
    else:
        print("❌ Initialize failed")
        return
    
    # Test tools/list
    print("\n2. Testing tools/list...")
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server.handle_request(list_request)
    if response and response.get("result"):
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    else:
        print("❌ Tools list failed")
        return
    
    # Test get_departures tool
    print("\n3. Testing get_departures tool...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_departures",
            "arguments": {"station_name": "Hauptbahnhof"}
        }
    }
    
    response = await server.handle_request(call_request)
    if response and response.get("result"):
        content = response["result"]["content"][0]["text"]
        print("✅ get_departures result:")
        print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print("❌ get_departures failed")
        if response and response.get("error"):
            print(f"   Error: {response['error']['message']}")
    
    # Test find_station tool
    print("\n4. Testing find_station tool...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "find_station",
            "arguments": {"station_name": "Marienplatz"}
        }
    }
    
    response = await server.handle_request(call_request)
    if response and response.get("result"):
        content = response["result"]["content"][0]["text"]
        print("✅ find_station result:")
        print(f"   {content}")
    else:
        print("❌ find_station failed")
        if response and response.get("error"):
            print(f"   Error: {response['error']['message']}")

if __name__ == "__main__":
    asyncio.run(test_mvg_mcp())