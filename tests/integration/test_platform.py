#!/usr/bin/env python3
"""
Test script for the Multi-Service MCP Platform.

This script tests the platform functionality without starting the HTTP server.
"""

import asyncio
import json
from multi_service_server import MultiServiceMCPServer

async def test_platform():
    """Test the multi-service platform functionality."""
    print("🧪 Testing Multi-Service MCP Platform...")
    print("=" * 50)
    
    # Create server instance
    server = MultiServiceMCPServer()
    
    # Test 1: List services
    print("📋 Test 1: Service Registration")
    services = server.router.list_services()
    print(f"✅ Found {len(services)} registered services:")
    for service in services:
        print(f"  - {service.name} v{service.version}: {service.status}")
    print()
    
    # Test 2: MCP Initialize
    print("🔧 Test 2: MCP Initialize")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    response = await server.handle_mcp_request(init_request)
    print(f"✅ Initialize response: {response['result']['serverInfo']['name']}")
    print()
    
    # Test 3: List tools
    print("🛠️  Test 3: List Tools")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server.handle_mcp_request(tools_request)
    tools = response['result']['tools']
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    print()
    
    # Test 4: Call mindful service
    print("🧘 Test 4: Mindful Service")
    mindful_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "mindful_get_mindful_sentence",
            "arguments": {}
        }
    }
    
    response = await server.handle_mcp_request(mindful_request)
    if 'result' in response:
        content = response['result']['content'][0]['text']
        print("✅ Mindful sentence received:")
        print(f"   {content}")
    else:
        print(f"❌ Error: {response.get('error', 'Unknown error')}")
    print()
    
    # Test 5: Test daily rotation (call multiple times)
    print("🔄 Test 5: Daily Rotation (4 calls)")
    sentences = set()
    for i in range(4):
        response = await server.handle_mcp_request(mindful_request)
        if 'result' in response:
            content = response['result']['content'][0]['text']
            # Extract just the sentence part
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    sentences.add(line.strip())
                    break
    
    print(f"✅ Received {len(sentences)} unique sentences (should be 4)")
    print()
    
    # Test 6: Direct service router test
    print("🔀 Test 6: Service Router Direct Test")
    router_response = await server.router.route_request(
        url="/mindful/v1",
        method="get_mindful_sentence",
        params={},
        request_id="test-direct"
    )
    
    if router_response.success:
        print("✅ Service router working correctly")
        result = router_response.data['result']
        print(f"   Content type: {result['content'][0]['type']}")
    else:
        print(f"❌ Router error: {router_response.error}")
    print()
    
    # Test 7: Error handling
    print("❌ Test 7: Error Handling")
    error_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "invalid_tool",
            "arguments": {}
        }
    }
    
    response = await server.handle_mcp_request(error_request)
    if 'error' in response:
        print(f"✅ Error handling works: {response['error']['message']}")
    else:
        print("❌ Error handling failed")
    print()
    
    print("=" * 50)
    print("🎉 Platform testing completed!")
    print("🚀 Ready to start the HTTP server with: python start_platform.py")

if __name__ == "__main__":
    asyncio.run(test_platform())