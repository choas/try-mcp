"""Tests for resource usage under load."""

import asyncio
import time
import pytest
import json
import statistics
import concurrent.futures
import psutil
import os
import threading
from fastapi.testclient import TestClient

from multi_service_server import app

client = TestClient(app)

@pytest.mark.performance
def test_resource_usage_under_load():
    """Test resource usage (CPU, memory) under load."""
    # Skip this test if psutil is not available
    pytest.importorskip("psutil")
    
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
        }
    ]
    
    # Function to make a single request
    def make_request(request_info):
        response = client.post(
            request_info["url"],
            json=request_info["json"]
        )
        return {
            "name": request_info["name"],
            "status_code": response.status_code
        }
    
    # Function to monitor resource usage
    def monitor_resources():
        process = psutil.Process(os.getpid())
        cpu_percentages = []
        memory_usages = []
        
        while monitoring:
            cpu_percentages.append(process.cpu_percent(interval=0.1))
            memory_usages.append(process.memory_info().rss / 1024 / 1024)  # Convert to MB
            time.sleep(0.1)
        
        return {
            "cpu_avg": statistics.mean(cpu_percentages) if cpu_percentages else 0,
            "cpu_max": max(cpu_percentages) if cpu_percentages else 0,
            "memory_avg": statistics.mean(memory_usages) if memory_usages else 0,
            "memory_max": max(memory_usages) if memory_usages else 0
        }
    
    # Start resource monitoring
    monitoring = True
    monitor_thread = threading.Thread(target=monitor_resources)
    monitor_thread.start()
    
    try:
        # Make concurrent requests
        num_concurrent = 20  # 20 concurrent requests per service
        all_requests = []
        for _ in range(num_concurrent):
            all_requests.extend(requests)
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
            results = list(executor.map(make_request, all_requests))
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Check that all requests succeeded
        for result in results:
            assert result["status_code"] == 200, f"Request to {result['name']} failed with status {result['status_code']}"
    
    finally:
        # Stop resource monitoring
        monitoring = False
        monitor_thread.join()
    
    # Get resource usage results
    resource_results = monitor_resources()
    
    print("\nResource Usage Under Load:")
    print(f"CPU Average: {resource_results['cpu_avg']:.2f}%")
    print(f"CPU Maximum: {resource_results['cpu_max']:.2f}%")
    print(f"Memory Average: {resource_results['memory_avg']:.2f} MB")
    print(f"Memory Maximum: {resource_results['memory_max']:.2f} MB")
    print(f"Total time for {len(results)} requests: {total_time:.2f}ms")
    print(f"Average time per request: {total_time / len(results):.2f}ms")
    
    # Resource usage assertions - these thresholds should be adjusted based on the expected resource usage
    # These are just example thresholds
    assert resource_results['cpu_max'] < 100, f"CPU usage ({resource_results['cpu_max']:.2f}%) exceeds threshold (100%)"
    assert resource_results['memory_max'] < 1000, f"Memory usage ({resource_results['memory_max']:.2f} MB) exceeds threshold (1000 MB)"