"""Digital fortune cookie service implementation."""

import hashlib
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.base_service import BaseService
from data.models import ToolResult
from data.fortune_prompts import get_fortune_prompts, get_fortune_generation_instructions

logger = logging.getLogger(__name__)


class FortuneService(BaseService):
    """Fortune cookie service providing surreal and cryptic phrases with hourly caching."""
    
    def __init__(self):
        """Initialize the fortune service."""
        super().__init__(
            name="fortune",
            version="v1",
            description="Digital fortune cookie service providing surreal and cryptic phrases that change hourly"
        )
        
        # Hourly cache for generated fortunes
        self._fortune_cache: Dict[str, str] = {}  # hour_key -> fortune_phrase
        self._prompts = get_fortune_prompts()
        self._generation_instructions = get_fortune_generation_instructions()

        self.add_resource(
            uri="fortune://generation-instructions",
            name="Fortune generation instructions",
            description="The style rules for writing a surreal fortune cookie phrase",
            read=lambda: self._generation_instructions,
            mime_type="text/plain"
        )
        self.add_resource(
            uri="fortune://inspirations",
            name="Fortune inspirations",
            description="The lines the fortune prompts and the get_fortune_cookie tool start from",
            read=lambda: {"count": len(self._prompts), "inspirations": self._prompts}
        )
        
        # Define the tools this service provides
        self._tool_definitions = [
            {
                "name": "get_fortune_cookie",
                "description": "Get a surreal and cryptic fortune cookie phrase. Same phrase is returned for the entire hour.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """Handle incoming fortune service requests.
        
        Args:
            method: The method/tool name to execute
            params: Parameters for the method
            
        Returns:
            ToolResult containing the response
        """
        try:
            if method == "get_fortune_cookie":
                return await self._handle_get_fortune_cookie(params)
            else:
                return self._create_error_response(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error in fortune service method {method}: {e}")
            return self._create_error_response(str(e))
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this service.
        
        Returns:
            List of tool definitions in MCP format
        """
        return self._tool_definitions.copy()
    
    async def _handle_get_fortune_cookie(self, params: Dict[str, Any]) -> ToolResult:
        """Handle get_fortune_cookie requests.
        
        Args:
            params: Request parameters (empty for this method)
            
        Returns:
            ToolResult with a fortune cookie phrase
        """
        current_hour = self._get_current_hour_key()
        
        # Check if we have a cached fortune for this hour
        if current_hour in self._fortune_cache:
            fortune_phrase = self._fortune_cache[current_hour]
            logger.info(f"Returning cached fortune for hour {current_hour}")
        else:
            # Generate a new fortune for this hour
            fortune_phrase = self._generate_fortune_phrase(current_hour)
            self._fortune_cache[current_hour] = fortune_phrase
            logger.info(f"Generated new fortune for hour {current_hour}")
        
        # Format the response as a fortune cookie
        result_text = f"🥠 Digital Fortune Cookie 🥠\n\n\"{fortune_phrase}\"\n\n✨ Contemplate the mystery within ✨"
        
        return self._create_text_response(result_text)
    

    
    def _get_current_hour_key(self) -> str:
        """Get a unique key for the current hour.
        
        Returns:
            String key representing the current hour (YYYY-MM-DD-HH format)
        """
        now = datetime.now(timezone.utc)
        return f"{now.year:04d}-{now.month:02d}-{now.day:02d}-{now.hour:02d}"
    
    def _generate_fortune_phrase(self, hour_key: str) -> str:
        """Generate a surreal and cryptic fortune phrase for the given hour.
        
        This simulates LLM generation by using deterministic randomization
        based on the hour key to ensure consistency within the hour.
        
        Args:
            hour_key: Unique key for the hour
            
        Returns:
            Generated fortune phrase
        """
        # Use hour key as seed for deterministic randomization
        seed_value = int(hashlib.md5(hour_key.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed_value)
        
        # Select a base prompt deterministically
        base_prompt = rng.choice(self._prompts)
        
        # Generate variations and combinations to create unique phrases
        fortune_templates = [
            "When {concept1}, {concept2} {action} in the realm of {concept3}",
            "The {object1} that {action1} {object2} reveals {wisdom}",
            "In the {place} of {concept1}, {concept2} {action} {object}",
            "What the {entity1} {action1}, the {entity2} {action2} in return",
            "Where {concept1} meets {concept2}, {result} blooms eternal",
            "The {object} {action} when {condition}, yet {paradox} remains",
            "Between {concept1} and {concept2}, {entity} {action} {object}",
            "As {concept1} {action1}, so {concept2} {action2} in {place}"
        ]
        
        # Word pools for generating variations
        concepts = ["silence", "shadow", "light", "time", "memory", "dream", "truth", "illusion", "wisdom", "mystery"]
        objects = ["mirror", "key", "door", "path", "bridge", "river", "mountain", "star", "seed", "flame"]
        actions = ["whispers", "dances", "flows", "transforms", "awakens", "remembers", "forgets", "reveals", "conceals", "blooms"]
        entities = ["seeker", "dreamer", "wanderer", "sage", "fool", "child", "elder", "spirit", "heart", "mind"]
        places = ["garden", "library", "crossroads", "threshold", "sanctuary", "labyrinth", "tower", "valley", "shore", "void"]
        
        # Sometimes use the base prompt directly, sometimes generate a variation
        if rng.random() < 0.3:  # 30% chance to use base prompt directly
            return base_prompt
        else:
            # Generate a new phrase using templates
            template = rng.choice(fortune_templates)
            
            # Fill in the template with random selections
            phrase = template.format(
                concept1=rng.choice(concepts),
                concept2=rng.choice(concepts),
                concept3=rng.choice(concepts),
                object1=rng.choice(objects),
                object2=rng.choice(objects),
                object=rng.choice(objects),
                action=rng.choice(actions),
                action1=rng.choice(actions),
                action2=rng.choice(actions),
                entity1=rng.choice(entities),
                entity2=rng.choice(entities),
                entity=rng.choice(entities),
                place=rng.choice(places),
                wisdom=f"the {rng.choice(concepts)} of {rng.choice(objects)}",
                result=f"{rng.choice(concepts)} and {rng.choice(concepts)}",
                condition=f"the {rng.choice(objects)} {rng.choice(actions)}",
                paradox=f"{rng.choice(concepts)} {rng.choice(actions)}"
            )
            
            return phrase
    
    def get_cached_fortune_count(self) -> int:
        """Get the number of cached fortunes.
        
        Returns:
            Number of cached fortune phrases
        """
        return len(self._fortune_cache)
    
    def clear_cache(self) -> None:
        """Clear the fortune cache (mainly for testing).
        """
        self._fortune_cache.clear()
    
    def get_fortune_for_hour(self, hour_key: str) -> Optional[str]:
        """Get the cached fortune for a specific hour.
        
        Args:
            hour_key: Hour key to look up
            
        Returns:
            Cached fortune phrase or None if not found
        """
        return self._fortune_cache.get(hour_key)
    
    def set_fortune_for_hour(self, hour_key: str, fortune: str) -> None:
        """Set a fortune for a specific hour (mainly for testing).
        
        Args:
            hour_key: Hour key
            fortune: Fortune phrase to cache
        """
        self._fortune_cache[hour_key] = fortune
    
    def supports_prompts(self) -> bool:
        """Check if this service supports MCP prompts.
        
        Returns:
            True since fortune service provides prompts
        """
        return True
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get MCP prompts provided by this service.
        
        Returns:
            List of prompt definitions in MCP format
        """
        prompts = []
        for i, prompt in enumerate(self._prompts):
            prompts.append({
                "name": f"fortune_prompt_{i+1}",
                "description": f"Fortune generation prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
                "arguments": []
            })
        return prompts

    def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Build the result of `prompts/get` for one of the fortune prompts."""
        for i, prompt in enumerate(self._prompts):
            if name == f"fortune_prompt_{i+1}":
                text = f"{self._generation_instructions}\n\nTake this line as inspiration:\n\"{prompt}\""
                return self._prompt_result(f"Fortune generation prompt: {prompt}", text)
        return None
