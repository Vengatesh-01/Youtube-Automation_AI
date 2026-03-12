<<<<<<< HEAD
import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import random
from utils import safe_print

# niche categories for viral educational shorts
NICHES = [
    "AI & Future Tech",
    "Human Psychology Secrets",
    "Space & Universe Mysteries",
    "Hidden History",
    "Wealth & Success Mindset",
    "Mind-Blowing Science"
]

FALLBACK_TOPICS = [
    {"title": "The AI Revolution", "description": "How artificial intelligence is changing the human race faster than any previous technology.", "category": "AI & Future Tech"},
    {"title": "The Dark Side of Psychology", "description": "Why your brain makes decisions before you even realize it.", "category": "Human Psychology Secrets"},
    {"title": "The Mystery of Black Holes", "description": "What actually happens when you cross the event horizon of a singularity?", "category": "Space & Universe Mysteries"},
    {"title": "The Lost City of Atlantis", "description": "New evidence suggesting the legendary civilization might have actually existed.", "category": "Hidden History"},
    {"title": "The 1% Mindset", "description": "The exact psychological traits that separate world-class achievers from everyone else.", "category": "Wealth & Success Mindset"},
    {"title": "Quantum Entanglement", "description": "The 'spooky action at a distance' that proves our universe is weirder than we thought.", "category": "Mind-Blowing Science"}
]

def generate_topics(count: int = 5) -> list:
    """Fetch trending topics or return niche-specific fallbacks."""
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    topics = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=10)
        root = ET.fromstring(response.read())
        for item in root.findall(".//item")[:count]:
            title = item.find("title").text
            desc_elem = item.find("description")
            description = desc_elem.text if desc_elem is not None else f"Trending topic: {title}"
            # Assign a random niche for variety
            topics.append({"title": title, "description": description, "category": random.choice(NICHES)})
        if topics:
            return topics
    except Exception as e:
        safe_print(f"Google Trends unavailable ({e}), using fallback topics.")
    
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
=======
import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import random

# niche categories for viral educational shorts
NICHES = [
    "AI & Future Tech",
    "Human Psychology Secrets",
    "Space & Universe Mysteries",
    "Hidden History",
    "Wealth & Success Mindset",
    "Mind-Blowing Science"
]

FALLBACK_TOPICS = [
    {"title": "The AI Revolution", "description": "How artificial intelligence is changing the human race faster than any previous technology.", "category": "AI & Future Tech"},
    {"title": "The Dark Side of Psychology", "description": "Why your brain makes decisions before you even realize it.", "category": "Human Psychology Secrets"},
    {"title": "The Mystery of Black Holes", "description": "What actually happens when you cross the event horizon of a singularity?", "category": "Space & Universe Mysteries"},
    {"title": "The Lost City of Atlantis", "description": "New evidence suggesting the legendary civilization might have actually existed.", "category": "Hidden History"},
    {"title": "The 1% Mindset", "description": "The exact psychological traits that separate world-class achievers from everyone else.", "category": "Wealth & Success Mindset"},
    {"title": "Quantum Entanglement", "description": "The 'spooky action at a distance' that proves our universe is weirder than we thought.", "category": "Mind-Blowing Science"}
]

def generate_topics(count: int = 5) -> list:
    """Fetch trending topics or return niche-specific fallbacks."""
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    topics = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=10)
        root = ET.fromstring(response.read())
        for item in root.findall(".//item")[:count]:
            title = item.find("title").text
            desc_elem = item.find("description")
            description = desc_elem.text if desc_elem is not None else f"Trending topic: {title}"
            # Assign a random niche for variety
            topics.append({"title": title, "description": description, "category": random.choice(NICHES)})
        if topics:
            return topics
    except Exception as e:
        print(f"Google Trends unavailable ({e}), using fallback topics.")
    
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
    print(f"Topic generated and saved to {filename}")
    return filename


if __name__ == "__main__":
    run()
>>>>>>> 5de9b8a010a88a45f95c4e78d34480178966007c
