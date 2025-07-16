"""Fortune cookie prompts for generating surreal and cryptic phrases."""

from typing import List


def get_fortune_prompts() -> List[str]:
    """Get a collection of surreal and cryptic prompts for fortune generation.
    
    Returns:
        List of prompts that can be used to generate fortune cookie phrases
    """
    return [
        "The mirror reflects not what is, but what dreams to be",
        "When the clock strikes thirteen, the impossible becomes inevitable",
        "The shadow of tomorrow whispers secrets to yesterday's echo",
        "In the garden of forgotten thoughts, new wisdom blooms backwards",
        "The key that opens no door unlocks everything",
        "Where silence speaks loudest, the deaf hear most clearly",
        "The river flows uphill when viewed from the moon's perspective",
        "What the butterfly remembers, the caterpillar never knew",
        "The empty cup holds the most precious tea",
        "When words fail, the spaces between them sing",
        "The shortest path is often a circle drawn in reverse",
        "What falls up must have forgotten how to remember down",
        "The lighthouse guides ships that sail through solid ground",
        "In the library of unwritten books, every page tells your story",
        "The compass points to where you've never been but always belonged",
        "When the sun sets in the east, the west remembers its youth",
        "The door that never opens is always ajar in dreams",
        "What the ocean forgets, the desert remembers in grains",
        "The tree grows its roots in the sky when no one is watching",
        "Where footprints lead backwards, the journey begins anew",
        "The candle burns brightest when the flame is extinguished",
        "What the wind carries away, it brings back transformed",
        "The mountain moves when it thinks no one is looking",
        "In the museum of lost moments, time stands perfectly still",
        "The bridge connects shores that exist only in possibility",
        "When the last star forgets to shine, darkness becomes light",
        "The seed knows the tree it will never become",
        "What the heart hides, the shadow reveals in daylight",
        "The circle completes itself by remaining forever unfinished",
        "Where the map ends, the real territory begins to unfold"
    ]


def get_fortune_generation_instructions() -> str:
    """Get instructions for generating fortune cookie phrases.
    
    Returns:
        Instructions for creating surreal and cryptic fortune phrases
    """
    return """Create a surreal and cryptic fortune cookie phrase that:
- Uses metaphorical and abstract language
- Contains elements of paradox or impossible scenarios
- Evokes a sense of mystery and wonder
- Is thought-provoking but not immediately clear in meaning
- Combines familiar concepts in unexpected ways
- Has a poetic or philosophical quality
- Is between 10-25 words long
- Avoids direct advice or obvious meanings
- Creates vivid imagery through unusual juxtapositions

The phrase should feel like it comes from a dream or alternate reality, 
leaving the reader to interpret its deeper meaning."""