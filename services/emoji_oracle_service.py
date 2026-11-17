"""Emoji oracle service implementation."""

import logging
from typing import Any, Dict, List

from services.base_service import BaseService
from data.models import ToolResult
from data.emoji_symbols import get_emoji_oracle_reading, get_emoji_pool

logger = logging.getLogger(__name__)


class EmojiOracleService(BaseService):
    """Emoji oracle service providing cryptic 3-emoji combinations with mystical messages."""
    
    def __init__(self):
        """Initialize the emoji oracle service."""
        super().__init__(
            name="emoji-oracle",
            version="v1",
            description="Emoji oracle service providing cryptic guidance through symbolic emoji combinations"
        )
        
        # Define the tools this service provides
        self._tool_definitions = [
            {
                "name": "get_emoji_oracle",
                "description": "Receive cryptic guidance through a combination of 3 meaningful emojis with mystical interpretation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

        self.add_prompt(
            name="ask_the_oracle",
            description="Ask the emoji oracle a question and get the reading interpreted",
            arguments=[{"name": "question", "description": "The question you want to ask the oracle", "required": False}],
            render=lambda args: (
                "Call the get_emoji_oracle tool and interpret the reading for me in three short sentences, "
                "one per emoji, in a playful and mysterious tone."
                + (f" My question to the oracle: {args['question']}" if "question" in args else "")
            )
        )
        self.add_resource(
            uri="emoji-oracle://symbols",
            name="Oracle symbols",
            description="All emoji symbols the oracle can draw, grouped by category",
            read=get_emoji_pool
        )
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming emoji oracle service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "get_emoji_oracle":
                return await self._handle_get_emoji_oracle(params)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in emoji oracle service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_get_emoji_oracle(self, params: Dict[str, Any]) -> ToolResult:
        """Handle get_emoji_oracle requests.
        
        Args:
            params: Request parameters (empty for this method)
            
        Returns:
            ToolResult with emoji oracle reading
        """
        # Generate the oracle reading
        reading = get_emoji_oracle_reading()
        
        logger.info(f"Generated emoji oracle reading: {reading['emoji_string']}")
        
        # Format the mystical response
        result_text = f"""🔮 The Emoji Oracle Speaks 🔮

{reading['emoji_string']}

{reading['message']}

✨ The symbols have aligned to reveal this cryptic wisdom. Meditate upon their meaning, for the universe speaks in mysterious ways... ✨"""
        
        return self._create_text_response(result_text)