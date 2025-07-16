"""Emoji symbol pool for the emoji oracle service."""

from typing import Dict, List
import random


def get_emoji_pool() -> Dict[str, List[str]]:
    """Get the categorized emoji symbol pool.
    
    Returns:
        Dictionary of emoji categories with their symbols
    """
    return {
        "nature": [
            "🌟", "🌙", "☀️", "🌊", "🌸", "🌿", "🍃", "🌺", "🌻", "🌷",
            "🌹", "🌵", "🌲", "🌳", "🍄", "🌾", "🌱", "🌼", "🌴", "🌈"
        ],
        "animals": [
            "🦋", "🐝", "🐞", "🕷️", "🦅", "🦉", "🐺", "🦊", "🐱", "🐶",
            "🐸", "🐢", "🦎", "🐍", "🦆", "🐧", "🦢", "🐙", "🦑", "🐠"
        ],
        "mystical": [
            "🔮", "✨", "⭐", "💫", "🌠", "🔯", "☯️", "🕯️", "🗝️", "👁️",
            "🧿", "🪬", "🔱", "⚡", "🌀", "💎", "🪄", "🧙", "🦄", "🐉"
        ],
        "objects": [
            "⚖️", "🗡️", "🛡️", "⚔️", "🏺", "📿", "🎭", "🎨", "🎪", "🎯",
            "🎲", "🃏", "🎴", "📚", "📜", "🗞️", "💌", "📮", "🎁", "🏆"
        ],
        "symbols": [
            "♠️", "♥️", "♦️", "♣️", "🔺", "🔻", "🔸", "🔹", "💠", "🔳",
            "🔲", "⬛", "⬜", "🟫", "🟪", "🟦", "🟩", "🟨", "🟧", "🟥"
        ],
        "celestial": [
            "🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🪐", "🌌",
            "☄️", "🛸", "🚀", "🛰️", "🌍", "🌎", "🌏", "🗺️", "🧭", "⏳"
        ],
        "elements": [
            "🔥", "💧", "🌪️", "❄️", "⛄", "🌋", "🏔️", "🏜️", "🏖️", "🌊",
            "💨", "⛅", "🌤️", "⛈️", "🌩️", "🌨️", "☔", "💦", "🧊", "💥"
        ]
    }


def get_random_emoji_combination(count: int = 3) -> List[str]:
    """Generate a random combination of emojis from different categories.
    
    Args:
        count: Number of emojis to select (default: 3)
        
    Returns:
        List of selected emojis
    """
    emoji_pool = get_emoji_pool()
    all_categories = list(emoji_pool.keys())
    selected_emojis = []
    
    # Try to select from different categories for more diverse combinations
    used_categories = set()
    
    for _ in range(count):
        # Get available categories (prefer unused ones)
        available_categories = [cat for cat in all_categories if cat not in used_categories]
        
        # If all categories used, reset and allow reuse
        if not available_categories:
            available_categories = all_categories
            used_categories.clear()
        
        # Select a random category
        category = random.choice(available_categories)
        used_categories.add(category)
        
        # Select a random emoji from that category
        emoji = random.choice(emoji_pool[category])
        selected_emojis.append(emoji)
    
    return selected_emojis


def generate_cryptic_message(emojis: List[str]) -> str:
    """Generate a cryptic message based on the emoji combination.
    
    Args:
        emojis: List of emojis to interpret
        
    Returns:
        Cryptic message string
    """
    # Cryptic message templates that can incorporate the emojis
    templates = [
        "The {0} whispers secrets to the {1}, while {2} watches from the shadows...",
        "When {0} meets {1}, the {2} reveals hidden truths.",
        "Three paths converge: {0} leads to wisdom, {1} to mystery, {2} to transformation.",
        "The oracle speaks: {0} guards the past, {1} illuminates the present, {2} shapes the future.",
        "In the realm of symbols, {0} and {1} dance around {2}, creating new possibilities.",
        "Beware the alignment of {0}, {1}, and {2} - for change approaches on silent wings.",
        "The ancient ones say: {0} calls to {1}, and together they awaken {2}.",
        "Three forces unite: {0} brings clarity, {1} brings power, {2} brings renewal.",
        "The cosmic message unfolds: {0} opens doors, {1} lights the way, {2} completes the circle.",
        "Symbols speak louder than words: {0} + {1} + {2} = a truth yet to be discovered."
    ]
    
    template = random.choice(templates)
    return template.format(*emojis)


def get_emoji_oracle_reading() -> Dict[str, any]:
    """Get a complete emoji oracle reading.
    
    Returns:
        Dictionary containing emojis and cryptic message
    """
    emojis = get_random_emoji_combination(3)
    message = generate_cryptic_message(emojis)
    
    return {
        "emojis": emojis,
        "message": message,
        "emoji_string": " ".join(emojis)
    }