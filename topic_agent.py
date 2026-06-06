import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import random
from utils import safe_print

# Strategic Niches for Viral YouTube Shorts
NICHES = [
    "Dark Psychology Secrets",
    "Social Dynamics & Power",
    "Body Language Mastery",
    "Mental Resilience & Stoicism",
    "High-Performance Habits",
    "Influence & Persuasion Tricks"
]

FALLBACK_TOPICS = [
    {"title": "The 3-Second Psychological Trick to Make Anyone Respect You instantly", "description": "A dark psychology hack used by billionaires.", "category": "Social Dynamics & Power"},
    {"title": "They Are Lying to You: The Eye-Contact Test", "description": "How to catch a liar using the 'triangle method'.", "category": "Body Language Mastery"},
    {"title": "The 'Dark Empath' Personality Explained", "description": "The most dangerous personality type in the room.", "category": "Dark Psychology Secrets"},
    {"title": "Why 99% of People Fail (And How to Be the 1%)", "description": "The brutal truth about success and stoicism.", "category": "Mental Resilience & Stoicism"},
    {"title": "The 'Mirroring' Manipulation Tactic", "description": "How to spot when someone is trying to control your mind.", "category": "Influence & Persuasion Tricks"},
    {"title": "Stop Being Nice: The 'Law of Power' They Don't Want You to Know", "description": "Why highly agreeable people always finish last.", "category": "High-Performance Habits"},
    {"title": "The 'Silence Strategy' That Makes People Obsess Over You", "description": "Why the less you say, the more powerful you seem.", "category": "Social Dynamics & Power"},
    {"title": "How to Read Minds in 5 Seconds", "description": "Micro-expressions that reveal exactly what someone is thinking.", "category": "Body Language Mastery"},
    {"title": "The Japanese Secret to Mental Invincibility (Kaizen)", "description": "How to build a mind that cannot be broken.", "category": "Mental Resilience & Stoicism"},
    {"title": "The Toxic 'Love Bombing' Trap", "description": "How to identify manipulation before it destroys you.", "category": "Dark Psychology Secrets"}
]

def generate_topics(count: int = 5) -> list:
    """Fetch niche-specific fallbacks (Google Trends RSS is deprecated and hangs on Render)."""
    # Mix fallbacks with random niche assignments
    all_fallbacks = FALLBACK_TOPICS.copy()
    random.shuffle(all_fallbacks)
    return all_fallbacks[:count]


def run():
    """Legacy entry point — saves first topic to file and returns the path."""
    topics = generate_topics(5)
    topic = topics[0]
    os.makedirs("topics", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"topics/topic_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(topic, f, indent=4)
    safe_print(f"Topic generated and saved to {filename}")
    return filename


if __name__ == "__main__":
    run()
