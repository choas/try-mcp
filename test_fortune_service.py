"""Unit tests for the fortune cookie service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from services.fortune_service import FortuneService
from data.models import ToolResult


class TestFortuneService:
    """Test cases for the FortuneService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = FortuneService()
    
    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        assert self.service.name == "fortune"
        assert self.service.version == "v1"
        assert "Digital fortune cookie service" in self.service.description
        assert self.service.get_status() == "active"
        assert len(self.service._prompts) > 0
        assert len(self.service._generation_instructions) > 0
    
    def test_get_tools(self):
        """Test that the service returns correct tool definitions."""
        tools = self.service.get_tools()
        
        # Should have both get_fortune_cookie and prompts/list
        assert len(tools) == 2
        
        tool_names = [tool["name"] for tool in tools]
        assert "get_fortune_cookie" in tool_names
        assert "prompts/list" in tool_names
        
        # Check get_fortune_cookie tool structure
        fortune_tool = next(tool for tool in tools if tool["name"] == "get_fortune_cookie")
        assert "surreal and cryptic" in fortune_tool["description"]
        assert fortune_tool["inputSchema"]["type"] == "object"
        assert fortune_tool["inputSchema"]["required"] == []
        
        # Check prompts/list tool structure
        prompts_tool = next(tool for tool in tools if tool["name"] == "prompts/list")
        assert "prompts" in prompts_tool["description"]
        assert prompts_tool["inputSchema"]["type"] == "object"
    
    @pytest.mark.asyncio
    async def test_handle_get_fortune_cookie(self):
        """Test handling get_fortune_cookie requests."""
        result = await self.service.handle_request("get_fortune_cookie", {})
        
        assert isinstance(result, ToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        text = result.content[0]["text"]
        assert "🥠 Digital Fortune Cookie 🥠" in text
        assert "✨ Contemplate the mystery within ✨" in text
        
        # Should contain a fortune phrase between the decorations
        lines = text.split('\n')
        fortune_line = None
        for line in lines:
            if line.startswith('"') and line.endswith('"'):
                fortune_line = line
                break
        
        assert fortune_line is not None
        assert len(fortune_line) > 2  # More than just quotes
    
    @pytest.mark.asyncio
    async def test_handle_prompts_list(self):
        """Test handling prompts/list requests."""
        result = await self.service.handle_request("prompts/list", {})
        
        assert isinstance(result, ToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        text = result.content[0]["text"]
        assert "📜 Fortune Cookie Prompts 📜" in text
        assert "Available prompts:" in text
        assert "Sample prompts:" in text
        assert "🎭 Generation Instructions 🎭" in text
        assert "surreal and cryptic" in text
    
    @pytest.mark.asyncio
    async def test_handle_unknown_method(self):
        """Test handling unknown method requests."""
        result = await self.service.handle_request("unknown_method", {})
        
        assert isinstance(result, ToolResult)
        assert result.is_error
        assert len(result.content) == 1
        assert "Unknown method: unknown_method" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_handle_request_exception(self):
        """Test handling exceptions during request processing."""
        # Mock the _handle_get_fortune_cookie method to raise an exception
        with patch.object(self.service, '_handle_get_fortune_cookie', side_effect=Exception("Test error")):
            result = await self.service.handle_request("get_fortune_cookie", {})
            
            assert isinstance(result, ToolResult)
            assert result.is_error
            assert "Test error" in result.content[0]["text"]
    
    def test_get_current_hour_key(self):
        """Test hour key generation."""
        # Mock datetime to control the current time
        mock_datetime = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        
        with patch('services.fortune_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_datetime
            
            hour_key = self.service._get_current_hour_key()
            assert hour_key == "2024-01-15-14"
    
    def test_generate_fortune_phrase_deterministic(self):
        """Test that fortune generation is deterministic for the same hour."""
        hour_key = "2024-01-15-14"
        
        # Generate fortune multiple times with same hour key
        fortune1 = self.service._generate_fortune_phrase(hour_key)
        fortune2 = self.service._generate_fortune_phrase(hour_key)
        fortune3 = self.service._generate_fortune_phrase(hour_key)
        
        # Should be identical
        assert fortune1 == fortune2 == fortune3
        assert len(fortune1) > 0
    
    def test_generate_fortune_phrase_different_hours(self):
        """Test that different hours generate different fortunes."""
        hour_key1 = "2024-01-15-14"
        hour_key2 = "2024-01-15-15"
        hour_key3 = "2024-01-16-14"
        
        fortune1 = self.service._generate_fortune_phrase(hour_key1)
        fortune2 = self.service._generate_fortune_phrase(hour_key2)
        fortune3 = self.service._generate_fortune_phrase(hour_key3)
        
        # Should be different (very high probability)
        assert fortune1 != fortune2
        assert fortune1 != fortune3
        assert fortune2 != fortune3
    
    def test_generate_fortune_phrase_uses_prompts(self):
        """Test that fortune generation sometimes uses base prompts."""
        hour_keys = [f"2024-01-15-{hour:02d}" for hour in range(24)]
        fortunes = [self.service._generate_fortune_phrase(key) for key in hour_keys]
        
        # At least some fortunes should match base prompts (30% chance each)
        base_prompts = set(self.service._prompts)
        matching_prompts = [f for f in fortunes if f in base_prompts]
        
        # With 24 attempts and 30% chance each, we should get at least a few matches
        assert len(matching_prompts) > 0
    
    @pytest.mark.asyncio
    async def test_hourly_caching_same_hour(self):
        """Test that the same fortune is returned within the same hour."""
        # Mock the current hour
        mock_hour = "2024-01-15-14"
        
        with patch.object(self.service, '_get_current_hour_key', return_value=mock_hour):
            # First call should generate and cache
            result1 = await self.service.handle_request("get_fortune_cookie", {})
            
            # Second call should return cached result
            result2 = await self.service.handle_request("get_fortune_cookie", {})
            
            # Results should be identical
            assert result1.content[0]["text"] == result2.content[0]["text"]
            
            # Cache should contain the fortune
            assert mock_hour in self.service._fortune_cache
    
    @pytest.mark.asyncio
    async def test_hourly_caching_different_hours(self):
        """Test that different hours generate different cached fortunes."""
        hour1 = "2024-01-15-14"
        hour2 = "2024-01-15-15"
        
        # First hour
        with patch.object(self.service, '_get_current_hour_key', return_value=hour1):
            result1 = await self.service.handle_request("get_fortune_cookie", {})
        
        # Second hour
        with patch.object(self.service, '_get_current_hour_key', return_value=hour2):
            result2 = await self.service.handle_request("get_fortune_cookie", {})
        
        # Results should be different
        assert result1.content[0]["text"] != result2.content[0]["text"]
        
        # Both hours should be cached
        assert hour1 in self.service._fortune_cache
        assert hour2 in self.service._fortune_cache
        assert self.service._fortune_cache[hour1] != self.service._fortune_cache[hour2]
    
    def test_cache_management_methods(self):
        """Test cache management utility methods."""
        # Initially empty
        assert self.service.get_cached_fortune_count() == 0
        
        # Add some test data
        self.service.set_fortune_for_hour("2024-01-15-14", "Test fortune 1")
        self.service.set_fortune_for_hour("2024-01-15-15", "Test fortune 2")
        
        assert self.service.get_cached_fortune_count() == 2
        assert self.service.get_fortune_for_hour("2024-01-15-14") == "Test fortune 1"
        assert self.service.get_fortune_for_hour("2024-01-15-15") == "Test fortune 2"
        assert self.service.get_fortune_for_hour("2024-01-15-16") is None
        
        # Clear cache
        self.service.clear_cache()
        assert self.service.get_cached_fortune_count() == 0
        assert self.service.get_fortune_for_hour("2024-01-15-14") is None
    
    def test_service_info(self):
        """Test service information retrieval."""
        service_info = self.service.get_service_info()
        
        assert service_info.name == "fortune"
        assert service_info.version == "v1"
        assert "Digital fortune cookie service" in service_info.description
        assert service_info.status == "active"
        assert len(service_info.tools) == 2
    
    def test_fortune_phrase_quality(self):
        """Test that generated fortune phrases meet quality criteria."""
        # Generate several fortunes to test
        hour_keys = [f"2024-01-15-{hour:02d}" for hour in range(10)]
        fortunes = [self.service._generate_fortune_phrase(key) for key in hour_keys]
        
        for fortune in fortunes:
            # Should be non-empty strings
            assert isinstance(fortune, str)
            assert len(fortune.strip()) > 0
            
            # Should be reasonable length (not too short or too long)
            word_count = len(fortune.split())
            assert 5 <= word_count <= 50  # Reasonable range for cryptic phrases
            
            # Should not contain obvious errors
            assert not fortune.startswith(" ")
            assert not fortune.endswith(" ")
    
    @pytest.mark.asyncio
    async def test_mcp_compliance(self):
        """Test MCP protocol compliance."""
        # Test that tools are properly formatted for MCP
        tools = self.service.get_tools()
        
        for tool in tools:
            # Required MCP tool fields
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            
            # Input schema should be valid JSON schema
            schema = tool["inputSchema"]
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
            assert isinstance(schema["required"], list)
        
        # Test that handle_request works with MCP methods
        result = await self.service.handle_request("get_fortune_cookie", {})
        assert isinstance(result, ToolResult)
        assert hasattr(result, 'content')
        assert hasattr(result, 'is_error')
        assert isinstance(result.content, list)
        assert isinstance(result.is_error, bool)


class TestFortuneServiceIntegration:
    """Integration tests for the fortune service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = FortuneService()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test the complete fortune cookie workflow."""
        # Get prompts list
        prompts_result = await self.service.handle_request("prompts/list", {})
        assert not prompts_result.is_error
        assert "Fortune Cookie Prompts" in prompts_result.content[0]["text"]
        
        # Get fortune cookie
        fortune_result = await self.service.handle_request("get_fortune_cookie", {})
        assert not fortune_result.is_error
        assert "Digital Fortune Cookie" in fortune_result.content[0]["text"]
        
        # Get another fortune in the same hour (should be same)
        fortune_result2 = await self.service.handle_request("get_fortune_cookie", {})
        assert fortune_result.content[0]["text"] == fortune_result2.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self):
        """Test that the service handles various error conditions gracefully."""
        # Test with invalid parameters (should still work since no params required)
        result = await self.service.handle_request("get_fortune_cookie", {"invalid": "param"})
        assert not result.is_error
        
        # Test with empty parameters
        result = await self.service.handle_request("get_fortune_cookie", {})
        assert not result.is_error
        
        # Test with None parameters
        result = await self.service.handle_request("get_fortune_cookie", None)
        assert not result.is_error
    
    def test_concurrent_access_simulation(self):
        """Test that the service can handle concurrent-like access patterns."""
        # Simulate multiple requests in the same hour
        hour_key = "2024-01-15-14"
        
        with patch.object(self.service, '_get_current_hour_key', return_value=hour_key):
            # Multiple calls should all get the same cached result
            fortunes = []
            for _ in range(5):
                fortune = self.service._generate_fortune_phrase(hour_key)
                fortunes.append(fortune)
            
            # All should be identical
            assert all(f == fortunes[0] for f in fortunes)
            
            # Cache should only have one entry
            self.service._fortune_cache[hour_key] = fortunes[0]
            assert self.service.get_cached_fortune_count() == 1