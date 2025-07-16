#!/usr/bin/env python3

import asyncio
import json
import aiohttp

async def test_http_mcp():
    """Test the HTTP MCP server."""
    print("Testing MVG MCP HTTP Server...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data['status']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
            print("Make sure to start the HTTP server first: python mcp_http_server.py")
            return
        
        # Test initialize
        print("\n2. Testing initialize...")
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
        
        async with session.post(f"{base_url}/mcp", json=init_request) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("result"):
                    print("✅ Initialize successful")
                    print(f"   Server: {data['result']['serverInfo']['name']}")
                else:
                    print("❌ Initialize failed")
                    return
            else:
                print(f"❌ Initialize failed: {response.status}")
                return
        
        # Test tools/list
        print("\n3. Testing tools/list...")
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        async with session.post(f"{base_url}/mcp", json=list_request) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("result"):
                    tools = data["result"]["tools"]
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"   - {tool['name']}: {tool['description']}")
                else:
                    print("❌ Tools list failed")
                    return
            else:
                print(f"❌ Tools list failed: {response.status}")
                return
        
        # Test get_departures tool
        print("\n4. Testing get_departures tool...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_departures",
                "arguments": {"station_name": "Hauptbahnhof"}
            }
        }
        
        async with session.post(f"{base_url}/mcp", json=call_request) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("result"):
                    content = data["result"]["content"][0]["text"]
                    print("✅ get_departures result:")
                    print(content[:200] + "..." if len(content) > 200 else content)
                else:
                    print("❌ get_departures failed")
                    if data.get("error"):
                        print(f"   Error: {data['error']['message']}")
            else:
                print(f"❌ get_departures failed: {response.status}")
        
        # Test find_station tool
        print("\n5. Testing find_station tool...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "find_station",
                "arguments": {"station_name": "Marienplatz"}
            }
        }
        
        async with session.post(f"{base_url}/mcp", json=call_request) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("result"):
                    content = data["result"]["content"][0]["text"]
                    print("✅ find_station result:")
                    print(f"   {content}")
                else:
                    print("❌ find_station failed")
                    if data.get("error"):
                        print(f"   Error: {data['error']['message']}")
            else:
                print(f"❌ find_station failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_http_mcp())