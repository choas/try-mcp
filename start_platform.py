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
    print("  • MCP Protocol: http://localhost:8003/mcp")
    print("  • Service List: http://localhost:8003/services")
    print("  • Health Check: http://localhost:8003/health")
    print("  • Documentation: http://localhost:8003/docs")
    print()
    
    print("🧘 Example Mindful Service Usage:")
    print("  curl -X POST http://localhost:8003/services/mindful/v1/get_mindful_sentence")
    print()
    
    print("🚇 Example MVG Service Usage:")
    print('  curl -X POST http://localhost:8003/services/mvg/v1/get_departures \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"station_name": "Hauptbahnhof"}\'')
    print()
    
    print("🔧 MCP Tool Usage (via MCP client):")
    print("  - mindful_get_mindful_sentence: Get inspirational sentence")
    print("  - mvg_get_departures: Get Munich transport departures")
    print("  - mvg_find_station: Find Munich transport station")
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