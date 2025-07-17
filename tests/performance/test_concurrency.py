"""Concurrency tests for the multi-service MCP platform."""

import asyncio
import time
import pytest
import json
import statistics
import concurrent.futures
from fastapi.testclient import TestClient

from multi_service_server import app

client = TestClient(app)

@pytest.mark.performance
def test_concurrent_requests():
    """Test handling of concurrent requests to different services."""
    # Define a list of requests to different services
    requests = [
        {
            "url": "/services/mindful/v1/get_mindful_sentence",
            "json": {},
            "name": "mindful"
        },
        {
            "url": "/services/weather/v1/get_weather_forecast",
            "json": {},
            "name": "weather"
        },
        {
            "url": "/services/emoji-oracle/v1/get_emoji_oracle",
            "json": {},
            "name": "emoji-oracle"
        },
        {
            "url": "/services/timestamp/v1/generate_random_timestamp",
            "json": {},
            "name": "timestamp"
        },
        {
            "url": "/services/fortune/v1/get_fortune_cookie",
            "json": {},
            "name": "fortune"
        },
        {
            "url": "/services/lucky-numbers/v1/generate_blessed_numbers",
            "json": {"scenario": "lottery", "count": 6},
            "name": "lucky-numbers"
        },
        {
            "url": "/services/mvg/v1/find_station",
            "json": {"query": "Hauptbahnhof", "limit": 3},
            "name": "mvg"
        }
    ]
    
    # Function to make a single request
    def make_request(request_info):
        start_time = time.time()
        response = client.post(
            request_info["url"],
            json=request_info["json"]
        )
        end_time = time.time()
        
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
        return {
            "name": request_info["name"],
            "status_code": response.status_code,
            "time_ms": elapsed
        }
    
    # Make concurrent requests
    num_concurrent = 10  # 10 concurrent requests per service
    all_requests = []
    for _ in range(num_concurrent):
        all_requests.extend(requests)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(make_request, all_requests))
    end_time = time.time()
    
    total_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Check that all requests succeeded
    for result in results:
        assert result["status_code"] == 200, f"Request to {result['name']} failed with status {result['status_code']}"
    
    # Calculate statistics per service
    service_times = {}
    for result in results:
        service_name = result["name"]
        if service_name not in service_times:
            service_times[service_name] = []
        service_times[service_name].append(result["time_ms"])
    
    print("\nConcurrent Request Results (in milliseconds):")
    print(f"{'Service':<20} {'Avg':<10} {'Min':<10} {'Max':<10} {'P95':<10}")
    print("-" * 60)
    
    for service, times in service_times.items():
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"{service:<20} {avg_time:<10.2f} {min_time:<10.2f} {max_time:<10.2f} {p95_time:<10.2f}")
        
        # Performance assertion - all services should handle concurrent requests within reasonable time
        assert avg_time < 1000, f"Service {service} average response time ({avg_time:.2f}ms) exceeds threshold (1000ms)"
    
    print(f"\nTotal time for {len(results)} concurrent requests: {total_time:.2f}ms")
    print(f"Average time per request: {total_time / len(results):.2f}ms")

@pytest.mark.performance
def test_concurrent_mcp_requests():
    """Test handling of concurrent requests to the MCP endpoint."""
    # Define a list of MCP requests
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "mindful_get_mindful_sentence",
                "arguments": {}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "weather_get_weather_forecast",
                "arguments": {}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "emoji-oracle_get_emoji_oracle",
                "arguments": {}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "timestamp_generate_random_timestamp",
                "arguments": {}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "fortune_get_fortune_cookie",
                "arguments": {}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "lucky-numbers_generate_blessed_numbers",
                "arguments": {"scenario": "lottery", "count": 6}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "mvg_find_station",
                "arguments": {"query": "Hauptbahnhof", "limit": 3}
            }
        }
    ]
    
    # Function to make a single MCP request
    def make_mcp_request(request_data):
        start_time = time.time()
        response = client.post(
            "/mcp",
            json=request_data
        )
        end_time = time.time()
        
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
        return {
            "id": request_data["id"],
            "status_code": response.status_code,
            "time_ms": elapsed
        }
    
    # Make concurrent requests
    num_concurrent = 5  # 5 concurrent requests per MCP call
    all_requests = []
    for _ in range(num_concurrent):
        all_requests.extend(requests)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(make_mcp_request, all_requests))
    end_time = time.time()
    
    total_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Check that all requests succeeded
    for result in results:
        assert result["status_code"] == 200, f"MCP request {result['id']} failed with status {result['status_code']}"
    
    # Calculate statistics
    times = [result["time_ms"] for result in results]
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print("\nConcurrent MCP Request Results (in milliseconds):")
    print(f"Average: {avg_time:.2f}ms")
    print(f"Minimum: {min_time:.2f}ms")
    print(f"Maximum: {max_time:.2f}ms")
    print(f"95th Percentile: {p95_time:.2f}ms")
    print(f"Total time for {len(results)} concurrent requests: {total_time:.2f}ms")
    print(f"Average time per request: {total_time / len(results):.2f}ms")
    
    # Performance assertion
    assert avg_time < 1000, f"MCP average response time ({avg_time:.2f}ms) exceeds threshold (1000ms)"