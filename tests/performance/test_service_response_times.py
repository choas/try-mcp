"""Performance tests for service response times."""

import asyncio
import time
import pytest
import json
from fastapi.testclient import TestClient
import statistics

from multi_service_server import app

client = TestClient(app)

# List of services and their test methods
SERVICE_METHODS = [
    {"service": "mindful", "method": "get_mindful_sentence", "params": {}},
    {"service": "weather", "method": "get_weather_forecast", "params": {}},
    {"service": "emoji-oracle", "method": "get_emoji_oracle", "params": {}},
    {"service": "timestamp", "method": "generate_random_timestamp", "params": {}},
    {"service": "fortune", "method": "get_fortune_cookie", "params": {}},
    {"service": "lucky-numbers", "method": "generate_blessed_numbers", "params": {"scenario": "lottery", "count": 6}},
]

@pytest.mark.performance
def test_service_response_times():
    """Test response times for all services."""
    results = {}
    
    for service_info in SERVICE_METHODS:
        service = service_info["service"]
        method = service_info["method"]
        params = service_info["params"]
        
        # Warm-up call
        response = client.post(
            f"/services/{service}/v1/{method}",
            json=params
        )
        
        # Actual timed calls
        times = []
        for _ in range(10):  # 10 calls per service
            start_time = time.time()
            response = client.post(
                f"/services/{service}/v1/{method}",
                json=params
            )
            end_time = time.time()
            
            assert response.status_code == 200, f"Service {service} failed with status {response.status_code}"
            
            elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
            times.append(elapsed)
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        results[f"{service}_{method}"] = {
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "p95_ms": p95_time
        }
        
        # Performance assertion - all services should respond within 500ms on average
        # This threshold can be adjusted based on the expected performance
        assert avg_time < 500, f"Service {service} average response time ({avg_time:.2f}ms) exceeds threshold (500ms)"
    
    # Print results in a readable format
    print("\nService Response Time Results (in milliseconds):")
    print(f"{'Service':<30} {'Avg':<10} {'Min':<10} {'Max':<10} {'P95':<10}")
    print("-" * 70)
    
    for service, metrics in results.items():
        print(f"{service:<30} {metrics['avg_ms']:<10.2f} {metrics['min_ms']:<10.2f} "
              f"{metrics['max_ms']:<10.2f} {metrics['p95_ms']:<10.2f}")

@pytest.mark.performance
def test_mcp_endpoint_performance():
    """Test performance of the main MCP endpoint."""
    # Test tools/list performance
    times = []
    for _ in range(10):
        start_time = time.time()
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    print(f"\nMCP tools/list average response time: {avg_time:.2f}ms")
    assert avg_time < 500, f"MCP tools/list average response time ({avg_time:.2f}ms) exceeds threshold (500ms)"
    
    # Test tools/call performance for a simple service
    times = []
    for _ in range(10):
        start_time = time.time()
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "mindful_get_mindful_sentence",
                    "arguments": {}
                }
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    print(f"MCP tools/call average response time: {avg_time:.2f}ms")
    assert avg_time < 500, f"MCP tools/call average response time ({avg_time:.2f}ms) exceeds threshold (500ms)"