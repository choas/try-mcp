"""Unit tests for the emoji oracle service."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from services.emoji_oracle_service import EmojiOracleService
from data.emoji_symbols import get_emoji_pool, get_random_emoji_combination, generate_cryptic_message, get_emoji_oracle_reading
from data.models import ToolResult


class TestEmojiSymbols:
    """Test the emoji symbols data module."""
    
    def test_get_emoji_pool_structure(self):
        """Test that emoji pool has correct structure and categories."""
        pool = get_emoji_pool()
        
        # Check that it's a dictionary
        assert isinstance(pool, dict)
        
        # Check expected categories exist
        expected_categories = ["nature", "animals", "mystical", "objects", "symbols", "celestial", "elements"]
        for category in expected_categories:
            assert category in pool
            assert isinstance(pool[category], list)
            assert len(pool[category]) > 0
    
    def test_emoji_pool_diversity(self):
        """Test that emoji pool has sufficient diversity."""
        pool = get_emoji_pool()
        
        # Check each category has reasonable number of emojis
        for category, emojis in pool.items():
            assert len(emojis) >= 15, f"Category {category} should have at least 15 emojis"
            
            # Check all items are strings (emojis)
            for emoji in emojis:
                assert isinstance(emoji, str)
                assert len(emoji) >= 1  # Emojis should be at least 1 character
    
    def test_get_random_emoji_combination_default(self):
        """Test random emoji combination with default parameters."""
        combination = get_random_emoji_combination()
        
        assert isinstance(combination, list)
        assert len(combination) == 3  # Default count
        
        # Check all items are strings
        for emoji in combination:
            assert isinstance(emoji, str)
    
    def test_get_random_emoji_combination_custom_count(self):
        """Test random emoji combination with custom count."""
        for count in [1, 2, 5, 10]:
            combination = get_random_emoji_combination(count)
            assert len(combination) == count
    
    def test_emoji_combination_uniqueness(self):
        """Test that multiple calls generate different combinations."""
        combinations = []
        for _ in range(10):
            combo = get_random_emoji_combination(3)
            combinations.append(tuple(combo))  # Convert to tuple for comparison
        
        # Should have some variety (not all identical)
        unique_combinations = set(combinations)
        assert len(unique_combinations) > 1, "Should generate different combinations"
    
    def test_emoji_combination_category_diversity(self):
        """Test that emoji combinations try to use different categories."""
        pool = get_emoji_pool()
        all_emojis_by_category = {}
        
        # Create reverse mapping: emoji -> category
        for category, emojis in pool.items():
            for emoji in emojis:
                all_emojis_by_category[emoji] = category
        
        # Generate multiple combinations and check category diversity
        diverse_combinations = 0
        for _ in range(20):
            combo = get_random_emoji_combination(3)
            categories = [all_emojis_by_category.get(emoji, "unknown") for emoji in combo]
            unique_categories = set(categories)
            
            if len(unique_categories) > 1:  # At least 2 different categories
                diverse_combinations += 1
        
        # Most combinations should have some category diversity
        assert diverse_combinations > 10, "Should generate combinations with category diversity"
    
    def test_generate_cryptic_message(self):
        """Test cryptic message generation."""
        test_emojis = ["🌟", "🦋", "🔮"]
        message = generate_cryptic_message(test_emojis)
        
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Message should contain all emojis
        for emoji in test_emojis:
            assert emoji in message
    
    def test_cryptic_message_variety(self):
        """Test that different emoji combinations generate different messages."""
        test_cases = [
            ["🌟", "🦋", "🔮"],
            ["🌙", "🐺", "⚡"],
            ["🌊", "🦅", "💎"]
        ]
        
        messages = []
        for emojis in test_cases:
            message = generate_cryptic_message(emojis)
            messages.append(message)
        
        # Should generate different messages (templates vary)
        unique_messages = set(messages)
        assert len(unique_messages) >= 2, "Should generate varied messages"
    
    def test_get_emoji_oracle_reading(self):
        """Test complete oracle reading generation."""
        reading = get_emoji_oracle_reading()
        
        assert isinstance(reading, dict)
        assert "emojis" in reading
        assert "message" in reading
        assert "emoji_string" in reading
        
        # Check emojis
        assert isinstance(reading["emojis"], list)
        assert len(reading["emojis"]) == 3
        
        # Check message
        assert isinstance(reading["message"], str)
        assert len(reading["message"]) > 0
        
        # Check emoji string
        assert isinstance(reading["emoji_string"], str)
        assert reading["emoji_string"] == " ".join(reading["emojis"])
        
        # Message should contain all emojis
        for emoji in reading["emojis"]:
            assert emoji in reading["message"]


class TestEmojiOracleService:
    """Test the emoji oracle service."""
    
    @pytest.fixture
    def service(self):
        """Create an emoji oracle service instance."""
        return EmojiOracleService()
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.name == "emoji-oracle"
        assert service.version == "v1"
        assert "emoji oracle" in service.description.lower()
        assert service.get_status() == "active"
    
    def test_get_tools(self, service):
        """Test get_tools method."""
        tools = service.get_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 1
        
        tool = tools[0]
        assert tool["name"] == "get_emoji_oracle"
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"
    
    def test_get_service_info(self, service):
        """Test get_service_info method."""
        info = service.get_service_info()
        
        assert info.name == "emoji-oracle"
        assert info.version == "v1"
        assert info.status == "active"
        assert len(info.tools) == 1
    
    @pytest.mark.asyncio
    async def test_handle_get_emoji_oracle(self, service):
        """Test handling get_emoji_oracle requests."""
        result = await service.handle_request("get_emoji_oracle", {})
        
        assert isinstance(result, ToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        text = result.content[0]["text"]
        assert "🔮 The Emoji Oracle Speaks 🔮" in text
        assert "✨" in text  # Should contain mystical elements
    
    @pytest.mark.asyncio
    async def test_handle_get_emoji_oracle_multiple_calls(self, service):
        """Test multiple calls to get_emoji_oracle generate different results."""
        results = []
        for _ in range(5):
            result = await service.handle_request("get_emoji_oracle", {})
            text = result.content[0]["text"]
            results.append(text)
        
        # Should generate different oracle readings
        unique_results = set(results)
        assert len(unique_results) > 1, "Should generate different oracle readings"
    
    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, service):
        """Test handling unknown method requests."""
        result = await service.handle_request("unknown_method", {})
        
        assert isinstance(result, ToolResult)
        assert result.is_error
        assert "Unknown method" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_handle_request_with_exception(self, service):
        """Test error handling when service method raises exception."""
        with patch('services.emoji_oracle_service.get_emoji_oracle_reading', side_effect=Exception("Test error")):
            result = await service.handle_request("get_emoji_oracle", {})
            
            assert isinstance(result, ToolResult)
            assert result.is_error
            assert "Error: Test error" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_oracle_reading_contains_emojis(self, service):
        """Test that oracle readings contain actual emojis."""
        result = await service.handle_request("get_emoji_oracle", {})
        text = result.content[0]["text"]
        
        # Should contain at least 3 emojis (the oracle combination)
        emoji_count = 0
        for char in text:
            # Simple check for emoji-like characters (Unicode ranges)
            if ord(char) > 0x1F000:  # Basic emoji range check
                emoji_count += 1
        
        assert emoji_count >= 3, "Should contain at least 3 emojis in the oracle reading"
    
    @pytest.mark.asyncio
    async def test_oracle_reading_format(self, service):
        """Test that oracle readings follow expected format."""
        result = await service.handle_request("get_emoji_oracle", {})
        text = result.content[0]["text"]
        
        # Check for expected format elements
        assert "🔮 The Emoji Oracle Speaks 🔮" in text
        assert "✨" in text
        assert "symbols have aligned" in text.lower() or "oracle speaks" in text.lower()
    
    def test_service_tool_definition_schema(self, service):
        """Test that tool definition has proper schema."""
        tools = service.get_tools()
        tool = tools[0]
        
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert isinstance(schema["required"], list)
        assert len(schema["required"]) == 0  # No required parameters


class TestEmojiOracleIntegration:
    """Integration tests for emoji oracle service."""
    
    @pytest.mark.asyncio
    async def test_emoji_oracle_end_to_end(self):
        """Test complete end-to-end emoji oracle functionality."""
        service = EmojiOracleService()
        
        # Test service registration info
        info = service.get_service_info()
        assert info.name == "emoji-oracle"
        
        # Test tool listing
        tools = service.get_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "get_emoji_oracle"
        
        # Test oracle reading
        result = await service.handle_request("get_emoji_oracle", {})
        assert not result.is_error
        
        text = result.content[0]["text"]
        
        # Verify oracle reading structure
        lines = text.split('\n')
        assert len(lines) >= 5  # Should have multiple lines
        
        # Should contain header
        assert any("Oracle Speaks" in line for line in lines)
        
        # Should contain emoji combination line
        emoji_line = None
        for line in lines:
            if line.strip() and not any(word in line for word in ["Oracle", "symbols", "universe", "wisdom"]):
                # This might be the emoji line
                if len(line.strip().split()) <= 5:  # Emoji lines are typically short
                    emoji_line = line.strip()
                    break
        
        assert emoji_line is not None, "Should contain emoji combination line"
    
    @pytest.mark.asyncio
    async def test_oracle_consistency_within_constraints(self):
        """Test that oracle maintains consistency within expected constraints."""
        service = EmojiOracleService()
        
        # Generate multiple readings
        readings = []
        for _ in range(10):
            result = await service.handle_request("get_emoji_oracle", {})
            text = result.content[0]["text"]
            readings.append(text)
        
        # All should follow same format
        for reading in readings:
            assert "🔮 The Emoji Oracle Speaks 🔮" in reading
            assert "✨" in reading
        
        # But content should vary
        unique_readings = set(readings)
        assert len(unique_readings) > 1, "Should generate varied oracle readings"


if __name__ == "__main__":
    pytest.main([__file__])