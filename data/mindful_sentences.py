"""Mindful sentences data pool for the mindful service."""

from typing import List

# Pool of 50+ inspirational and mindful sentences
MINDFUL_SENTENCES: List[str] = [
    "Take a deep breath and embrace this moment with gratitude.",
    "Every step you take is a chance to grow and learn something new.",
    "Your thoughts are like clouds - observe them and let them pass.",
    "In stillness, you find the strength to face any challenge.",
    "Kindness to yourself opens the door to kindness toward others.",
    "This moment is a gift - that's why it's called the present.",
    "Your breath is an anchor that brings you back to now.",
    "Progress, not perfection, is the path to lasting change.",
    "Listen to your inner wisdom - it knows the way forward.",
    "Every ending is also a new beginning waiting to unfold.",
    "You are exactly where you need to be in this moment.",
    "Compassion for yourself creates space for healing and growth.",
    "The journey of a thousand miles begins with a single mindful step.",
    "Your heart knows truths that your mind is still learning.",
    "In accepting what is, you find the power to create what could be.",
    "Silence is not empty - it's full of answers waiting to be heard.",
    "Each breath is a reminder that you are alive and capable.",
    "Your struggles are not signs of weakness, but of your humanity.",
    "Peace is not the absence of chaos, but calm within it.",
    "Trust the process - even when you can't see the whole path.",
    "Your presence is a gift to the world, just as you are.",
    "Mindfulness is not about emptying your mind, but filling it with awareness.",
    "Every moment offers a fresh start and a new perspective.",
    "You have survived 100% of your difficult days so far.",
    "Gratitude transforms what we have into enough.",
    "Your inner light shines brightest when you're being authentic.",
    "Patience with yourself is the foundation of all other patience.",
    "The present moment is the only time where life actually happens.",
    "Your thoughts don't define you - your response to them does.",
    "In letting go, you make space for something better to arrive.",
    "Every person you meet is fighting a battle you know nothing about.",
    "Your worth is not determined by your productivity or achievements.",
    "Sometimes the most productive thing you can do is rest.",
    "Mindful awareness turns ordinary moments into extraordinary ones.",
    "You are not your thoughts - you are the observer of your thoughts.",
    "Gentle persistence opens doors that force cannot budge.",
    "Your sensitivity is not a weakness - it's a superpower.",
    "The art of living is finding balance between holding on and letting go.",
    "Every breath is a chance to begin again with fresh intention.",
    "Your journey is unique - don't compare it to anyone else's path.",
    "In stillness, solutions often appear that action couldn't find.",
    "You are both the artist and the masterpiece of your own life.",
    "Mindfulness is the practice of coming home to yourself.",
    "Your emotions are visitors - acknowledge them, but don't let them move in.",
    "The most important relationship you'll ever have is with yourself.",
    "Every challenge is an invitation to discover your hidden strength.",
    "Your breath connects you to this moment and to all of life.",
    "Wisdom often comes disguised as ordinary moments of clarity.",
    "You don't have to be perfect to be worthy of love and respect.",
    "The seeds of tomorrow's joy are planted in today's mindful moments.",
    "Your inner peace is not dependent on external circumstances.",
    "Every act of self-compassion ripples out into the world as kindness.",
    "The present moment is where your power to choose resides.",
    "Your authentic self is the greatest gift you can offer the world.",
    "Mindfulness is not about stopping thoughts, but changing your relationship with them."
]


def get_sentence_pool() -> List[str]:
    """Get the complete pool of mindful sentences.
    
    Returns:
        List of all available mindful sentences
    """
    return MINDFUL_SENTENCES.copy()


def get_sentence_count() -> int:
    """Get the total number of sentences in the pool.
    
    Returns:
        Number of sentences available
    """
    return len(MINDFUL_SENTENCES)