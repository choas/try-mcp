"""Unit tests for the mindful service."""

import pytest
from datetime import date
from unittest.mock import patch

from services.mindful_service import MindfulService
from data.mindful_sentences import get_sentence_count


class TestMindfulService:
    """Test cases for the MindfulService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = MindfulService()
    
    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        assert self.service.name == "mindful"
        assert self.service.version == "v1"
        assert "inspirational" in self.service.description.lower()
        assert self.service.get_status() == "active"
    
    def test_get_tools(self):
        """Test that the service returns correct tool definitions."""
        tools = self.service.get_tools()
        assert len(tools) == 1
        
        tool = tools[0]
        assert tool["name"] == "get_mindful_sentence"
        assert "inspirational" in tool["description"].lower()
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"
    
    @pytest.mark.asyncio
    async def test_get_mindful_sentence_basic(self):
        """Test basic mindful sentence retrieval."""
        result = await self.service.handle_request("get_mindful_sentence", {})
        
        assert not result.is_error
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        
        text = result.content[0]["text"]
        assert "🧘 Mindful Moment 🧘" in text
        assert "✨ Take a moment to reflect on these words ✨" in text
    
    @pytest.mark.asyncio
    async def test_daily_sentence_rotation(self):
        """Test that 4 different sentences are provided per day."""
        sentences_received = set()
        
        # Request sentences multiple times
        for _ in range(10):  # Request more than 4 to test cycling
            result = await self.service.handle_request("get_mindful_sentence", {})
            assert not result.is_error
            
            text = result.content[0]["text"]
            # Extract the actual sentence (between the emoji decorations)
            lines = text.split('\n')
            sentence_line = None
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    sentence_line = line.strip()
                    break
            
            if sentence_line:
                sentences_received.add(sentence_line)
        
        # Should have exactly 4 different sentences for the day
        assert len(sentences_received) == 4
    
    @pytest.mark.asyncio
    async def test_sentence_count_tracking(self):
        """Test that daily sentence count is tracked correctly."""
        # Initially no sentences used today
        assert self.service.get_daily_sentence_count() == 0
        
        # Request sentences and verify count increases
        for expected_count in range(1, 5):
            await self.service.handle_request("get_mindful_sentence", {})
            assert self.service.get_daily_sentence_count() == expected_count
        
        # After 4 sentences, count should stay at 4
        await self.service.handle_request("get_mindful_sentence", {})
        assert self.service.get_daily_sentence_count() == 4
    
    @pytest.mark.asyncio
    async def test_different_dates_independent(self):
        """Test that different dates have independent sentence tracking."""
        from datetime import date, timedelta
        
        # Get sentences for today
        today = date.today()
        for _ in range(2):
            await self.service.handle_request("get_mindful_sentence", {})
        
        today_count = self.service.get_daily_sentence_count(today)
        assert today_count == 2
        
        # Simulate yesterday (by manipulating the internal state)
        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.isoformat()
        self.service._daily_sentences[yesterday_str] = {10, 20, 30}  # 3 sentences
        
        # Verify counts are independent
        assert self.service.get_daily_sentence_count(today) == 2
        assert self.service.get_daily_sentence_count(yesterday) == 3
    
    @pytest.mark.asyncio
    async def test_sentence_pool_size(self):
        """Test that the sentence pool has at least 50 sentences."""
        sentence_count = get_sentence_count()
        assert sentence_count >= 50
        
        # Verify service has access to the full pool
        assert len(self.service._sentence_pool) == sentence_count
    
    @pytest.mark.asyncio
    async def test_reset_daily_sentences(self):
        """Test resetting daily sentence tracking."""
        # Get some sentences
        for _ in range(3):
            await self.service.handle_request("get_mindful_sentence", {})
        
        assert self.service.get_daily_sentence_count() == 3
        
        # Reset and verify
        self.service.reset_daily_sentences()
        assert self.service.get_daily_sentence_count() == 0
    
    @pytest.mark.asyncio
    async def test_get_used_sentences_today(self):
        """Test getting the set of used sentence indices."""
        # Initially empty
        used = self.service.get_used_sentences_today()
        assert len(used) == 0
        
        # Get some sentences
        for _ in range(3):
            await self.service.handle_request("get_mindful_sentence", {})
        
        used = self.service.get_used_sentences_today()
        assert len(used) == 3
        assert all(isinstance(idx, int) for idx in used)
        assert all(0 <= idx < len(self.service._sentence_pool) for idx in used)
    
    @pytest.mark.asyncio
    async def test_sentence_cycling_after_four(self):
        """Test that sentences cycle through the same 4 after reaching the limit."""
        # Get the first 4 sentences
        first_four_sentences = set()
        for _ in range(4):
            result = await self.service.handle_request("get_mindful_sentence", {})
            text = result.content[0]["text"]
            # Extract sentence
            lines = text.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    first_four_sentences.add(line.strip())
                    break
        
        # Get more sentences and verify they're from the same set
        for _ in range(10):  # Get many more
            result = await self.service.handle_request("get_mindful_sentence", {})
            text = result.content[0]["text"]
            # Extract sentence
            lines = text.split('\n')
            sentence_found = False
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    assert line.strip() in first_four_sentences
                    sentence_found = True
                    break
            assert sentence_found
    
    @pytest.mark.asyncio
    async def test_unknown_method_error(self):
        """Test error handling for unknown methods."""
        result = await self.service.handle_request("unknown_method", {})
        
        assert result.is_error
        assert "Unknown method: unknown_method" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_service_info(self):
        """Test service information retrieval."""
        info = self.service.get_service_info()
        
        assert info.name == "mindful"
        assert info.version == "v1"
        assert info.status == "active"
        assert len(info.tools) == 1
        assert info.tools[0]["name"] == "get_mindful_sentence"
    
    @pytest.mark.asyncio
    async def test_sentence_content_quality(self):
        """Test that sentences meet quality requirements."""
        # Get a few sentences and verify they're meaningful
        for _ in range(5):
            result = await self.service.handle_request("get_mindful_sentence", {})
            text = result.content[0]["text"]
            
            # Extract the actual sentence
            lines = text.split('\n')
            sentence = None
            for line in lines:
                if line.strip() and not line.startswith('🧘') and not line.startswith('✨'):
                    sentence = line.strip()
                    break
            
            assert sentence is not None
            assert len(sentence) > 10  # Should be meaningful length
            assert sentence.endswith('.')  # Should be complete sentences
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_same_day(self):
        """Test that concurrent requests on the same day work correctly."""
        import asyncio
        
        # Make multiple concurrent requests
        tasks = [
            self.service.handle_request("get_mindful_sentence", {})
            for _ in range(8)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(not result.is_error for result in results)
        
        # Should still respect the 4-sentence limit
        assert self.service.get_daily_sentence_count() == 4


if __name__ == "__main__":
    pytest.main([__file__])