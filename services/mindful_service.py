"""Mindful sentences service implementation."""

import logging
import random
from datetime import date
from typing import Any, Dict, List, Set

from services.base_service import BaseService
from data.models import ToolResult
from data.mindful_sentences import get_sentence_pool

logger = logging.getLogger(__name__)


class MindfulService(BaseService):
    """Mindful service providing inspirational sentences with daily rotation."""
    
    def __init__(self):
        """Initialize the mindful service."""
        super().__init__(
            name="mindful",
            version="v1",
            description="Mindful sentences service providing inspirational content with daily rotation"
        )
        
        # Track daily sentence usage
        self._daily_sentences: Dict[str, Set[int]] = {}  # date_str -> set of used sentence indices
        self._sentence_pool = get_sentence_pool()
        
        # Define the tools this service provides
        self._tool_definitions = [
            {
                "name": "get_mindful_sentence",
                "description": "Get an inspirational mindful sentence. Returns 4 different sentences per day.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming mindful service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "get_mindful_sentence":
                return await self._handle_get_mindful_sentence(params)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in mindful service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_get_mindful_sentence(self, params: Dict[str, Any]) -> ToolResult:
        """Handle get_mindful_sentence requests.
        
        Args:
            params: Request parameters (empty for this method)
            
        Returns:
            ToolResult with a mindful sentence
        """
        today = date.today().isoformat()
        
        # Initialize today's sentence tracking if needed
        if today not in self._daily_sentences:
            self._daily_sentences[today] = set()
        
        used_today = self._daily_sentences[today]
        
        # If we've already provided 4 sentences today, cycle through them
        if len(used_today) >= 4:
            # Reset and start over with the same 4 sentences for the day
            sentence_indices = list(used_today)
            selected_index = random.choice(sentence_indices)
        else:
            # Select a new sentence that hasn't been used today
            available_indices = [i for i in range(len(self._sentence_pool)) if i not in used_today]
            
            if not available_indices:
                # This shouldn't happen with 50+ sentences, but handle gracefully
                selected_index = random.randint(0, len(self._sentence_pool) - 1)
            else:
                selected_index = random.choice(available_indices)
                self._daily_sentences[today].add(selected_index)
        
        sentence = self._sentence_pool[selected_index]
        
        logger.info(f"Providing mindful sentence {selected_index} for {today}")
        
        # Format the response with some mindful presentation
        result_text = f"🧘 Mindful Moment 🧘\n\n{sentence}\n\n✨ Take a moment to reflect on these words ✨"
        
        return self._create_text_response(result_text)
    
    def get_daily_sentence_count(self, target_date: date = None) -> int:
        """Get the number of different sentences provided for a specific date.
        
        Args:
            target_date: Date to check (defaults to today)
            
        Returns:
            Number of different sentences provided on that date
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        return len(self._daily_sentences.get(date_str, set()))
    
    def reset_daily_sentences(self, target_date: date = None) -> None:
        """Reset sentence tracking for a specific date (mainly for testing).
        
        Args:
            target_date: Date to reset (defaults to today)
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        if date_str in self._daily_sentences:
            del self._daily_sentences[date_str]
    
    def get_used_sentences_today(self) -> Set[int]:
        """Get the set of sentence indices used today.
        
        Returns:
            Set of sentence indices used today
        """
        today = date.today().isoformat()
        return self._daily_sentences.get(today, set()).copy()