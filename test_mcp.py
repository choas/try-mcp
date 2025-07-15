#!/usr/bin/env python3

import asyncio
import json
import sys
from mcp_service import get_departures, get_station_id

async def test_mcp_functions():
    """Test the underlying MCP service functions."""
    print("Testing MCP Service Functions...")
    
    # Test get_station_id
    print("\n1. Testing get_station_id...")
    try:
        station_id = await get_station_id("Hauptbahnhof")
        if station_id:
            print(f"✅ Found Hauptbahnhof with ID: {station_id}")
        else:
            print("❌ Could not find Hauptbahnhof")
    except Exception as e:
        print(f"❌ Error getting station ID: {e}")
    
    # Test get_departures
    print("\n2. Testing get_departures...")
    try:
        departures = await get_departures("Hauptbahnhof")
        if departures:
            print(f"✅ Found {len(departures)} departures from Hauptbahnhof:")
            for i, dep in enumerate(departures[:3]):  # Show first 3
                print(f"  {i+1}. {dep['time']} | {dep['line']} → {dep['destination']}")
            if len(departures) > 3:
                print(f"  ... and {len(departures) - 3} more")
        else:
            print("❌ No departures found")
    except Exception as e:
        print(f"❌ Error getting departures: {e}")
    
    # Test with another station
    print("\n3. Testing with Marienplatz...")
    try:
        departures = await get_departures("Marienplatz")
        if departures:
            print(f"✅ Found {len(departures)} departures from Marienplatz")
        else:
            print("❌ No departures found for Marienplatz")
    except Exception as e:
        print(f"❌ Error getting Marienplatz departures: {e}")

async def test_mcp_server_handlers():
    """Test the MCP server handlers directly."""
    print("\n" + "="*50)
    print("Testing MCP Server Handlers...")
    
    # Import the handlers from mcp_server
    try:
        from mcp_server import handle_list_tools, handle_call_tool
        
        # Test list_tools
        print("\n1. Testing list_tools handler...")
        tools_result = await handle_list_tools()
        print(f"✅ Available tools: {len(tools_result.tools)}")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test call_tool with get_departures
        print("\n2. Testing call_tool handler with get_departures...")
        result = await handle_call_tool("get_departures", {"station_name": "Hauptbahnhof"})
        print("✅ get_departures result:")
        for content in result.content:
            print(content.text[:200] + "..." if len(content.text) > 200 else content.text)
        
        # Test call_tool with find_station
        print("\n3. Testing call_tool handler with find_station...")
        result = await handle_call_tool("find_station", {"station_name": "Marienplatz"})
        print("✅ find_station result:")
        for content in result.content:
            print(content.text)
            
    except Exception as e:
        print(f"❌ Error testing MCP server handlers: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_functions())
    asyncio.run(test_mcp_server_handlers())