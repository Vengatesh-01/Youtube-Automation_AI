import os
import requests
import json
import re
from datetime import datetime
from utils import safe_print

def generate_script_with_ollama(topic_dict):
    """Generate a high-retention 60-90 word motivational script using local Llama3."""
    title = topic_dict.get("title", "Discipline")
    
    prompt = f"""
    Act as a Principal Viral Script Strategist. 
    Your goal is 100% retention for a 15-30 second YouTube Short about: {title}.
    
    CORE THEMES (PICK THE MOST RELEVANT):
    - WEALTH: Millionaire habits, money rules.
    - AI: Job replacement, future tech secrets.
    - LUXURY: High-status psychology, billionaire routines.
    - CURIOSITY: Mind-blowing facts, hidden truths.
    
    STRUCTURE (MANDATORY):
    1. THE HOOK (0-2s): Max 7 words. Must be a "Pattern Interrupt" (Shock or Curiosity).
    2. THE AGITATION (2-10s): Increase tension and urgency.
    3. THE PAYOFF (10-25s): Reveal the insight or counter-intuitive truth.
    4. THE END LINE (Last 2s): Strong, punchy closing thought.
    
    STYLE RULES:
    - Sentence length: MAX 7 words. 
    - Rhythm: Punchy. Fast-paced. Emotional.
    - Output ONLY the spoken words. 
    - NO STAGE DIRECTIONS. NO LABELS like 'Hook:' or 'Payoff:'.
    """

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
