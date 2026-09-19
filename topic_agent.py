import os
import json
import random
import uuid
from datetime import datetime
from utils import safe_print

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

USED_TOPICS_FILE = os.path.abspath("videos/used_topics.json")

NICHES = [
    "Dark Psychology Secrets",
    "Social Dynamics & Power",
    "Body Language Mastery",
    "Mental Resilience & Stoicism",
    "High-Performance Habits",
    "Influence & Persuasion Tricks"
]

FALLBACK_TOPICS = [
    {"title": "The 3-Second Psychological Trick to Make Anyone Respect You instantly", "category": "Social Dynamics & Power"},
    {"title": "They Are Lying to You: The Eye-Contact Test", "category": "Body Language Mastery"},
    {"title": "The 'Dark Empath' Personality Explained", "category": "Dark Psychology Secrets"},
    {"title": "Why 99% of People Fail (And How to Be the 1%)", "category": "Mental Resilience & Stoicism"},
    {"title": "The 'Mirroring' Manipulation Tactic", "category": "Influence & Persuasion Tricks"},
    {"title": "Stop Being Nice: The 'Law of Power' They Don't Want You to Know", "category": "High-Performance Habits"},
    {"title": "The 'Silence Strategy' That Makes People Obsess Over You", "category": "Social Dynamics & Power"},
    {"title": "How to Read Minds in 5 Seconds", "category": "Body Language Mastery"},
    {"title": "The Japanese Secret to Mental Invincibility (Kaizen)", "category": "Mental Resilience & Stoicism"},
    {"title": "The Toxic 'Love Bombing' Trap", "category": "Dark Psychology Secrets"},
    {"title": "Why Sigma Males Always Win in Silence", "category": "Social Dynamics & Power"},
    {"title": "The 'Gaslighting' Red Flags You Must Never Ignore", "category": "Dark Psychology Secrets"},
    {"title": "The 1% Rule That Changes Everything", "category": "High-Performance Habits"},
    {"title": "Mastering the Art of Not Reacting", "category": "Mental Resilience & Stoicism"},
    {"title": "How to Build Unshakeable Confidence", "category": "Social Dynamics & Power"},
    {"title": "The Body Language of a True Leader", "category": "Body Language Mastery"},
    {"title": "Use This Persuasion Trick to Get What You Want", "category": "Influence & Persuasion Tricks"},
    {"title": "How to Spot a Fake Friend Instantly", "category": "Dark Psychology Secrets"},
    {"title": "The Stoic Guide to Overcoming Anxiety", "category": "Mental Resilience & Stoicism"},
    {"title": "Why Waking Up at 4 AM is a Cheat Code", "category": "High-Performance Habits"},
    {"title": "The Power of Saying 'No'", "category": "Mental Resilience & Stoicism"},
    {"title": "How to Read Micro-Expressions Like an FBI Agent", "category": "Body Language Mastery"},
    {"title": "The 'Guilt Trip' Manipulation Tactic Exposed", "category": "Dark Psychology Secrets"},
    {"title": "The Secret to Charismatic Storytelling", "category": "Influence & Persuasion Tricks"},
    {"title": "How to Build a Mindset of Steel", "category": "Mental Resilience & Stoicism"}
]

def load_used_topics():
    if os.path.exists(USED_TOPICS_FILE):
        try:
            with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_used_topic(title):
    used = load_used_topics()
    used.append(title)
    if len(used) > 100:  # Keep list manageable
        used = used[-100:]
    os.makedirs(os.path.dirname(USED_TOPICS_FILE), exist_ok=True)
    try:
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(used, f, indent=4)
    except Exception as e:
        safe_print(f"[TOPIC] Error saving used topic: {e}")

def get_gemini_topic():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import requests
        niche = random.choice(NICHES)
        prompt = (
            f"You are a master YouTube Shorts strategist. Generate 1 highly viral, clickbaity, and unique topic idea for a YouTube Short in the '{niche}' niche.\n\n"
            "Rules:\n"
            "1. Output exactly a valid JSON object, and nothing else.\n"
            "2. Format: {\"title\": \"The Viral Title Here\", \"category\": \"The Niche Here\"}\n"
            "3. The title should be highly engaging and between 5-12 words.\n"
            f"4. UNIQUENESS SEED: {uuid.uuid4().hex}"
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 1.2, "responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text']
            # try parsing json
            data = json.loads(text.strip('```json').strip('```').strip())
            if "title" in data and "category" in data:
                return data
    except Exception as e:
        safe_print(f"[TOPIC] Gemini generation failed: {e}")
    return None

def generate_topics(count: int = 5) -> list:
    """Generate unique topics, prioritizing Gemini API with fallback to a diverse pool."""
    used_titles = load_used_topics()
    topics = []
    
    # Try Gemini first for the first topic if count > 0
    if count > 0:
        gemini_topic = get_gemini_topic()
        if gemini_topic and gemini_topic["title"] not in used_titles:
            topics.append(gemini_topic)
            save_used_topic(gemini_topic["title"])
            used_titles.append(gemini_topic["title"])
            safe_print(f"[TOPIC] Generated fresh Gemini topic: {gemini_topic['title']}")
            count -= 1

    # Fill the rest with fallbacks
    available_fallbacks = [t for t in FALLBACK_TOPICS if t["title"] not in used_titles]
    
    # If we run out of fresh fallbacks, just shuffle the whole pool (should rarely happen with 25+ pool and 100 history max)
    if len(available_fallbacks) < count:
        available_fallbacks = FALLBACK_TOPICS.copy()
        
    random.shuffle(available_fallbacks)
    
    for t in available_fallbacks[:count]:
        topics.append(t)
        save_used_topic(t["title"])
        used_titles.append(t["title"])
        safe_print(f"[TOPIC] Using fallback topic: {t['title']}")
        
    return topics

def run():
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
