import os
import requests
import json
import re
from datetime import datetime

def generate_script_with_ollama(topic_dict):
    """Generate a high-retention 60-90 word motivational script using local Llama3."""
    title = topic_dict.get("title", "Discipline")
    
    prompt = f"""
You are a professional YouTube Shorts scriptwriter for a motivational channel like 'Excuse Eraser'.
Write a VERY CONCISE motivational and educational script about: {title}

RULES:
1. Tone: Motivational, clear, and engaging.
2. Hook: Start with a powerful shocking fact, curiosity question, or surprising statement.
3. Length: STRICTLY between 60 to 90 words total. BE SHORT.
<<<<<<< HEAD
4. Format: You MUST return the script exactly in this scene format:

Scene 1:
[Powerful Hook]

Scene 2:
[Explanation of the concept]

Scene 3:
[A relatable example]

Scene 4:
[The key lesson]

Scene 5:
[Motivational ending/Call to action]
=======
4. Format: You MUST return the script in this specific format for each scene:

Scene 1:
[Text to speak] | VISUAL: [Character pose like walking, sitting, reacting] | TEXT: [Short 1-3 word overlay]

Scene 2:
...and so on.

RULES FOR VISUALS:
- Describe a realistic character action that matches the content (e.g., "sitting on a bench looking sad", "walking confidently", "reacting with a surprised face").
- Keep visual descriptions to under 10 words.
- Ensure the character is consistent (Pixar style).
>>>>>>> clean_main

Do not include any other text, labels, or intros. Just Scene 1 to Scene 5.
"""

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
<<<<<<< HEAD
        response = requests.post(url, json=payload, timeout=60)
=======
        response = requests.post(url, json=payload, timeout=180)
>>>>>>> clean_main
        response.raise_for_status()
        result = response.json()
        raw_script = result.get("response", "").strip()
        
        # Basic validation to ensure "Scene" markers exist
        if "Scene 1" not in raw_script or "Scene 5" not in raw_script:
            print("⚠️ Ollama output format mismatch. Falling back to structured parsing attempt.")
            
        return raw_script
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

def generate_script(topic: dict) -> str:
    """Generate script using local Ollama model."""
    print(f"🚀 [SCRIPT] Generating local Llama3 script for: {topic.get('title')}")
    
    script_text = generate_script_with_ollama(topic)
    
    if not script_text:
        # Emergency minimal fallback if Ollama is down
        script_text = (
            "Scene 1:\n95% of people fail because they quit too early.\n\n"
            "Scene 2:\nSuccess is a marathon, not a sprint.\n\n"
            "Scene 3:\nThink of an athlete training in the dark.\n\n"
            "Scene 4:\nConsistency beats intensity every single time.\n\n"
            "Scene 5:\nKeep going. Your future self is counting on you!"
        )

    os.makedirs("scripts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_file = f"scripts/script_{timestamp}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    print(f"✅ Local AI script generated and saved to {script_file}")
    
    # Optional: Auto-sync to cloud if running in auto-mode
    if os.environ.get("AUTO_SYNC_TO_CLOUD") == "true":
        sync_to_github()
        
    return script_file

def sync_to_github():
    """Automatically push new scripts to GitHub so Render can see them."""
    print("☁️ [SYNC] Pushing new scripts to GitHub...")
    try:
        import subprocess
        subprocess.run(["git", "add", "scripts/*.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "Automated AI script generation"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ [SYNC] Successfully pushed to Cloud!")
    except Exception as e:
        print(f"❌ [SYNC] Error pushing to GitHub: {e}")


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            topic = json.load(f)
        generate_script(topic)
    else:
        print("Usage: python script_agent.py <path_to_topic_json>")
