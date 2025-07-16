#!/usr/bin/env python3

import asyncio
import json
import aiohttp
import sys

async def test_sse_mcp():
    """Test the SSE MCP server."""
    print("Testing MVG MCP SSE Server...")
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data['status']}")
                    print(f"   Active connections: {data['active_connections']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
            print("Make sure to start the SSE server first: python mcp_sse_server.py")
            return
        
        # Test standard HTTP MCP endpoint
        print("\n2. Testing standard MCP endpoint...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
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
                    capabilities = data['result']['capabilities']
                    if capabilities.get('transport', {}).get('streamable'):
                        print("   ✅ Streamable transport supported")
                    if capabilities.get('transport', {}).get('sse'):
                        print("   ✅ SSE transport supported")
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
        
        # Test SSE streaming (basic connection test)
        print("\n5. Testing SSE streaming...")
        try:
            async with session.get(f"{base_url}/mcp/stream") as response:
                if response.status == 200:
                    print("✅ SSE connection established")
                    
                    # Read a few SSE events
                    count = 0
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                print(f"   📡 SSE event: {data.get('type', 'unknown')}")
                                count += 1
                                if count >= 2:  # Just test a couple events
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"❌ SSE connection failed: {response.status}")
        except asyncio.TimeoutError:
            print("✅ SSE connection timeout (expected for test)")
        except Exception as e:
            print(f"❌ SSE test error: {e}")

async def test_sse_interactive():
    """Interactive SSE test - keeps connection open."""
    print("\n🔄 Starting interactive SSE test...")
    print("This will keep an SSE connection open. Press Ctrl+C to stop.")
    
    base_url = "http://localhost:8001"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/mcp/stream") as response:
                if response.status == 200:
                    print("✅ SSE connection established")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                print(f"📡 {data}")
                            except json.JSONDecodeError:
                                print(f"📡 Raw: {line}")
                else:
                    print(f"❌ SSE connection failed: {response.status}")
    except KeyboardInterrupt:
        print("\n👋 SSE test stopped by user")
    except Exception as e:
        print(f"❌ SSE error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(test_sse_interactive())
    else:
        asyncio.run(test_sse_mcp())