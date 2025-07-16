#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_simple_sse():
    """Simple test for SSE endpoint."""
    print("Testing SSE endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic endpoints first
            print("1. Testing health endpoint...")
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health: {data['status']}")
                else:
                    print(f"❌ Health failed: {response.status}")
                    return
            
            print("2. Testing root endpoint...")
            async with session.get("http://localhost:8001/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Service: {data['service']}")
                else:
                    print(f"❌ Root failed: {response.status}")
                    return
            
            print("3. Testing MCP info endpoint...")
            async with session.get("http://localhost:8001/mcp") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ MCP info: {data['service']}")
                else:
                    print(f"❌ MCP info failed: {response.status}")
                    return
            
            print("4. Testing SSE stream (will timeout after 5 seconds)...")
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get("http://localhost:8001/mcp/stream", timeout=timeout) as response:
                    if response.status == 200:
                        print("✅ SSE connection established")
                        
                        # Read a few lines
                        count = 0
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    data = json.loads(line_str[6:])
                                    print(f"   📡 SSE: {data}")
                                    count += 1
                                    if count >= 2:
                                        break
                                except json.JSONDecodeError:
                                    print(f"   📡 Raw: {line_str}")
                    else:
                        print(f"❌ SSE failed: {response.status}")
            except asyncio.TimeoutError:
                print("✅ SSE timeout (expected)")
            except Exception as e:
                print(f"❌ SSE error: {e}")
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the SSE server is running: python mcp_sse_server.py")

if __name__ == "__main__":
    asyncio.run(test_simple_sse())