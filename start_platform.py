#!/usr/bin/env python3
"""
Startup script for the Multi-Service MCP Platform.

This script starts the multi-service platform with all registered services.
"""

import asyncio
import logging
import sys
from multi_service_server import mcp_server, app
import uvicorn

def main():
    """Main startup function."""
    print("🚀 Starting Multi-Service MCP Platform...")
    print("=" * 50)
    
    # Display registered services
    services = mcp_server.router.list_services()
    print(f"📋 Registered Services ({len(services)}):")
    for service in services:
        print(f"  ✅ {service.name} v{service.version}")
        print(f"     📝 {service.description}")
        print(f"     🔧 Tools: {len(service.tools)}")
        for tool in service.tools:
            print(f"        - {tool['name']}: {tool['description']}")
        print()
    
    print("🌐 Server Endpoints:")
    print("  • Platform Info: http://localhost:8003")
    print("  • Service List: http://localhost:8003/services")
    print("  • Health Check: http://localhost:8003/health")
    print("  • Documentation: http://localhost:8003/docs")
    print()
    
    print("🧘 Mindful Service Endpoints:")
    print("  • MCP Protocol: http://localhost:8003/services/mindful/v1")
    print("  • Direct REST: http://localhost:8003/services/mindful/v1/get_mindful_sentence")
    print()
    
    print("🚇 MVG Service Endpoints:")
    print("  • MCP Protocol: http://localhost:8003/services/mvg/v1")
    print("  • Direct REST: http://localhost:8003/services/mvg/v1/get_departures")
    print("  • Direct REST: http://localhost:8003/services/mvg/v1/find_station")
    print()
    
    print("🌤️ Weather Service Endpoints:")
    print("  • MCP Protocol: http://localhost:8003/services/weather/v1")
    print("  • Direct REST: http://localhost:8003/services/weather/v1/get_weather_forecast")
    print()
    
    print("📡 MCP Protocol Examples:")
    print("  # Initialize Mindful Service")
    print('  curl -X POST http://localhost:8003/services/mindful/v1 \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\'')
    print()
    print("  # Get Mindful Sentence via MCP")
    print('  curl -X POST http://localhost:8003/services/mindful/v1 \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_mindful_sentence", "arguments": {}}}\'')
    print()
    print("  # Get Weather Forecast via MCP")
    print('  curl -X POST http://localhost:8003/services/weather/v1 \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_weather_forecast", "arguments": {"location": "Berlin"}}}\'')
    print()
    
    print("🔧 Direct REST API Examples:")
    print("  # Get Mindful Sentence")
    print("  curl -X POST http://localhost:8003/services/mindful/v1/get_mindful_sentence")
    print()
    print("  # Get MVG Departures")
    print('  curl -X POST http://localhost:8003/services/mvg/v1/get_departures \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"station_name": "Hauptbahnhof"}\'')
    print()
    print("  # Get Weather Forecast")
    print('  curl -X POST http://localhost:8003/services/weather/v1/get_weather_forecast \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"location": "Tokyo"}\'')
    print()
    
    print("🎯 Key Benefits:")
    print("  ✅ Each service has its own dedicated MCP endpoint")
    print("  ✅ Services are completely isolated and independent")
    print("  ✅ Both MCP protocol and REST API support")
    print("  ✅ No mixing of tools between services")
    print()
    
    print("=" * 50)
    print("🎯 Platform starting on http://localhost:8003")
    print("📊 Logs will be written to: multi_service_platform.log")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8003,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Multi-Service MCP Platform...")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()