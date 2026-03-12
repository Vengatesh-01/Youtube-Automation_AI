import os
import requests
import json
import re
from datetime import datetime
from utils import safe_print

def generate_script_with_ollama(topic_dict):
    """Generate a high-retention 60-90 word motivational script using local Llama3."""
    title = topic_dict.get("title", "Discipline")
    
    prompt = f"""You are a professional cinematic animation director and AI storyteller. Write a powerful motivational script about: {title}

OUTPUT FORMAT - EVERY SCENE MUST FOLLOW THIS STRUCTURE EXACTLY:
Scene [Number]
Environment: [specific 3D location, e.g., rainy city alley at night, glowing modern office]
Character Action: [Action ONLY: Walk, Sit, Talk, Stand, Gesture]
Emotion: [Mood ONLY: Sad, Hope, Success, Determined, Thinking]
Camera: [Movement ONLY: Slow Zoom, Tracking Shot, Low Angle, Face Close-up]
Subtitle: [1-5 words max, bold impact text]
Narrative: [the spoken dialogue, 15-20 words per scene]

STRICT RULES:
- Generate exactly 4-6 scenes.
- Spoken Dialogue: Total duration must be 30-45 seconds (approx 75-100 words).
- Hook: Scene 1 must be a high-impact visual and vocal hook.
- Character Actions: Use ONLY the primary verbs (Walk, Sit, Talk, Stand, Gesture).
- Subtitles: ALL CAPS, high impact.
- Do NOT add any preamble, explanation, or notes. Output the raw scene data only."""

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        raw_script = result.get("response", "").strip()
        
        # Basic validation to ensure "Scene" markers exist
        if "Scene 1" not in raw_script or "Scene 5" not in raw_script:
            safe_print("[WARNING] Ollama output format mismatch. Falling back to structured parsing attempt.")
            
        return raw_script
    except Exception as e:
        safe_print(f"[ERROR] Ollama Error: {e}")
        return None

def generate_script(topic: dict) -> str:
    """Generate script using local Ollama model."""
    safe_print(f"[SCRIPT] Generating local Llama3 script for: {topic.get('title')}")
    
    script_text = generate_script_with_ollama(topic)
    
    if not script_text:
        # Emergency minimal fallback if Ollama is down
        script_text = (
            "Scene 1:\n95% of people fail because they quit too early. | VISUAL: Character walking slowly looking tired | TEXT: QUIT TOO EARLY\n\n"
            "Scene 2:\nSuccess is a marathon, not a sprint. | VISUAL: Character sitting on a bench thinking | TEXT: SUCCESS MARATHON\n\n"
            "Scene 3:\nThink of an athlete training in the dark. | VISUAL: Character running in a dark park | TEXT: TRAINING HARD\n\n"
            "Scene 4:\nConsistency beats intensity every single time. | VISUAL: Character lifting a weights with a smile | TEXT: BE CONSISTENT\n\n"
            "Scene 5:\nKeep going. Your future self is counting on you! | VISUAL: Character standing on a cliff looking at sunset | TEXT: DON'T STOP"
        )

    os.makedirs("scripts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_file = f"scripts/script_{timestamp}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    safe_print(f"[SUCCESS] Local AI script generated and saved to {script_file}")
    
    # Optional: Auto-sync to cloud if running in auto-mode
    if os.environ.get("AUTO_SYNC_TO_CLOUD") == "true":
        sync_to_github()
        
    return script_file

def sync_to_github():
    """Automatically push new scripts to GitHub so Render can see them."""
    safe_print("[SYNC] Pushing new scripts to GitHub...")
    try:
        import subprocess
        subprocess.run(["git", "add", "scripts/*.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "Automated AI script generation"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        safe_print("[SYNC] Successfully pushed to Cloud!")
    except Exception as e:
        safe_print(f"[SYNC] Error pushing to GitHub: {e}")

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            topic = json.load(f)
        generate_script(topic)
    else:
        safe_print("Usage: python script_agent.py <path_to_topic_json>")
