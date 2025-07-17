"""
Helper functions for tests.
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

def load_fixture(filename: str) -> Dict[str, Any]:
    """Load a fixture file from the fixtures directory.
    
    Args:
        filename: Name of the fixture file
        
    Returns:
        Dictionary containing the fixture data
    """
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    file_path = os.path.join(fixtures_dir, filename)
    with open(file_path, "r") as f:
        return json.load(f)

def get_sample_request(request_type: str) -> Dict[str, Any]:
    """Get a sample request from the sample_requests.json fixture.
    
    Args:
        request_type: Type of request to get
        
    Returns:
        Dictionary containing the request data
    """
    requests = load_fixture("sample_requests.json")
    return requests.get(request_type, {})

def get_expected_response(response_type: str) -> Dict[str, Any]:
    """Get an expected response from the expected_responses.json fixture.
    
    Args:
        response_type: Type of response to get
        
    Returns:
        Dictionary containing the expected response data
    """
    responses = load_fixture("expected_responses.json")
    return responses.get(response_type, {})

def generate_random_string(length: int = 10) -> str:
    """Generate a random string of fixed length.
    
    Args:
        length: Length of the string to generate
        
    Returns:
        Random string
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def generate_random_datetime(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> datetime:
    """Generate a random datetime between start_date and end_date.
    
    Args:
        start_date: Start date (default: 1 year ago)
        end_date: End date (default: now)
        
    Returns:
        Random datetime
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()
        
    time_delta = end_date - start_date
    random_seconds = random.randint(0, int(time_delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def generate_random_mcp_request(
    method: str = "tools/call",
    service: str = "lucky-numbers",
    tool: str = "generate_blessed_numbers",
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate a random MCP request.
    
    Args:
        method: MCP method
        service: Service name
        tool: Tool name
        params: Parameters for the tool
        
    Returns:
        Dictionary containing the MCP request
    """
    if params is None:
        params = {"param1": "value1", "param2": "value2"}
        
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": {
            "name": f"{service}_{tool}",
            "arguments": params
        },
        "id": f"test-{generate_random_string(5)}"
    }

def assert_datetime_format(datetime_str: str) -> bool:
    """Assert that a string is in ISO 8601 datetime format with time component.
    
    Args:
        datetime_str: String to check
        
    Returns:
        True if the string is in ISO 8601 format with time component, False otherwise
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        # Check that it has a time component (not just a date)
        return dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0
    except ValueError:
        return False

def assert_response_has_required_fields(response: Dict[str, Any], required_fields: List[str]) -> bool:
    """Assert that a response has all required fields.
    
    Args:
        response: Response dictionary
        required_fields: List of required field names
        
    Returns:
        True if the response has all required fields, False otherwise
    """
    return all(field in response for field in required_fields)

def assert_mcp_response_format(response: Dict[str, Any]) -> bool:
    """Assert that a response follows the MCP format.
    
    Args:
        response: Response dictionary
        
    Returns:
        True if the response follows the MCP format, False otherwise
    """
    if "jsonrpc" not in response or response["jsonrpc"] != "2.0":
        return False
    if "id" not in response:
        return False
    if "result" not in response and "error" not in response:
        return False
    return True