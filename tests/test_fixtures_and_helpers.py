"""
Tests for the fixtures and helpers.
"""

import pytest
import os
from datetime import datetime
from tests.helpers import (
    load_fixture,
    get_sample_request,
    get_expected_response,
    generate_random_string,
    generate_random_datetime,
    generate_random_mcp_request,
    assert_datetime_format,
    assert_response_has_required_fields,
    assert_mcp_response_format
)

def test_load_fixture():
    """Test loading a fixture file."""
    fixture = load_fixture("sample_requests.json")
    assert isinstance(fixture, dict)
    assert "tools_list" in fixture
    assert "tools_call_lucky_numbers" in fixture

def test_get_sample_request():
    """Test getting a sample request."""
    request = get_sample_request("tools_list")
    assert isinstance(request, dict)
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "tools/list"
    assert request["id"] == "test-id"

def test_get_expected_response():
    """Test getting an expected response."""
    response = get_expected_response("lucky_numbers_success")
    assert isinstance(response, dict)
    assert "blessed_numbers" in response
    assert "scenario" in response
    assert response["status"] == "success"

def test_generate_random_string():
    """Test generating a random string."""
    string1 = generate_random_string()
    string2 = generate_random_string()
    assert isinstance(string1, str)
    assert len(string1) == 10
    assert string1 != string2  # Very unlikely to be equal

def test_generate_random_datetime():
    """Test generating a random datetime."""
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2020, 12, 31)
    random_date = generate_random_datetime(start_date, end_date)
    assert isinstance(random_date, datetime)
    assert start_date <= random_date <= end_date

def test_generate_random_mcp_request():
    """Test generating a random MCP request."""
    request = generate_random_mcp_request()
    assert isinstance(request, dict)
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "tools/call"
    assert "params" in request
    assert "name" in request["params"]
    assert "arguments" in request["params"]
    assert "id" in request

def test_assert_datetime_format():
    """Test asserting datetime format."""
    assert assert_datetime_format("2023-01-01T12:00:00")
    assert not assert_datetime_format("2023-01-01")
    assert not assert_datetime_format("invalid")

def test_assert_response_has_required_fields():
    """Test asserting response has required fields."""
    response = {"field1": "value1", "field2": "value2", "field3": "value3"}
    assert assert_response_has_required_fields(response, ["field1", "field2"])
    assert not assert_response_has_required_fields(response, ["field1", "field4"])

def test_assert_mcp_response_format():
    """Test asserting MCP response format."""
    valid_response = {
        "jsonrpc": "2.0",
        "id": "test-id",
        "result": {"content": [{"type": "text", "text": "Test"}]}
    }
    assert assert_mcp_response_format(valid_response)
    
    invalid_response1 = {
        "id": "test-id",
        "result": {"content": [{"type": "text", "text": "Test"}]}
    }
    assert not assert_mcp_response_format(invalid_response1)
    
    invalid_response2 = {
        "jsonrpc": "2.0",
        "id": "test-id"
    }
    assert not assert_mcp_response_format(invalid_response2)

# Test the fixtures from conftest.py
def test_fixed_datetime_fixture(fixed_datetime):
    """Test the fixed_datetime fixture."""
    assert isinstance(fixed_datetime, datetime)
    assert fixed_datetime.year == 2023
    assert fixed_datetime.month == 1
    assert fixed_datetime.day == 1

def test_test_client_fixture(test_client):
    """Test the test_client fixture."""
    assert test_client is not None

def test_sample_tool_result_fixture(sample_tool_result):
    """Test the sample_tool_result fixture."""
    assert sample_tool_result is not None
    assert not sample_tool_result.is_error
    assert len(sample_tool_result.content) > 0
    assert sample_tool_result.content[0]["type"] == "text"

def test_error_tool_result_fixture(error_tool_result):
    """Test the error_tool_result fixture."""
    assert error_tool_result is not None
    assert error_tool_result.is_error
    assert len(error_tool_result.content) > 0
    assert error_tool_result.content[0]["type"] == "text"
    assert "Error" in error_tool_result.content[0]["text"]

def test_sample_mcp_request_fixture(sample_mcp_request):
    """Test the sample_mcp_request fixture."""
    assert sample_mcp_request is not None
    assert sample_mcp_request["jsonrpc"] == "2.0"
    assert "method" in sample_mcp_request
    assert "params" in sample_mcp_request
    assert "id" in sample_mcp_request

def test_sample_mcp_response_fixture(sample_mcp_response):
    """Test the sample_mcp_response fixture."""
    assert sample_mcp_response is not None
    assert sample_mcp_response["jsonrpc"] == "2.0"
    assert "id" in sample_mcp_response
    assert "result" in sample_mcp_response