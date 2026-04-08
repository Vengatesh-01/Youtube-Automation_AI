import os
import json
import re
from datetime import datetime
from utils import safe_print

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_fallback_script(topic_title=None):
    safe_print(f"[SCRIPT] Generating static fallback script for: {topic_title or 'Unknown'}")
    return (
        "TITLE:\n"
        "The Only Rule To Never Giving Up\n\n"
        "DESCRIPTION:\n"
        "Are you feeling down? Remember this stoic principle. #stoicism #mindset #grind #motivation\n\n"
        "TAGS:\n"
        "stoicism, motivation, mindset, success, discipline\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        "Scene 1:\n"
        "Text: Character walking slowly looking tired\n"
        "Image Prompt: Pixar-style 3D animation, Disney cinematic lighting, emotional scene, handsome young man walking slowly looking tired, dark lighting\n"
        "Voiceover: 95% of people fail because they quit too early.\n"
        "Duration: 5s\n\n"
        "Scene 2:\n"
        "Text: Character sitting on a bench thinking\n"
        "Image Prompt: Pixar-style 3D animation, Disney cinematic lighting, emotional scene, handsome young man sitting on a bench thinking, soft volumetric light\n"
        "Voiceover: Success is a marathon, not a sprint.\n"
        "Duration: 5s\n\n"
        "Scene 3:\n"
        "Text: Character running in a dark park\n"
        "Image Prompt: Pixar-style 3D animation, Disney cinematic lighting, emotional scene, handsome young man running in a dark park, determined, rainy reflection\n"
        "Voiceover: Think of an athlete training in the dark.\n"
        "Duration: 5s\n\n"
        "Scene 4:\n"
        "Text: Character lifting weights with a smile\n"
        "Image Prompt: Pixar-style 3D animation, Disney cinematic lighting, emotional scene, handsome young man lifting a weights with a small smile, vibrant colors\n"
        "Voiceover: Consistency beats intensity every single time.\n"
        "Duration: 5s\n\n"
        "Scene 5:\n"
        "Text: Character standing on a cliff looking at sunset\n"
        "Image Prompt: Pixar-style 3D animation, Disney cinematic lighting, emotional scene, handsome young man standing on a high cliff looking at glowing sunset\n"
        "Voiceover: Keep going. Your future self is counting on you!\n"
        "Duration: 5s\n"
    )

def generate_script(topic: dict) -> str:
    """Generate script using Gemini API; falls back to static content if unavailable."""
    title = topic.get('title', 'Unknown Topic')
    safe_print(f"[SCRIPT] Generating script for: {title}")

    script_text = ""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Try using Gemini API
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "gemini_system.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    system_rules = f.read()
            else:
                system_rules = "Create a 5-scene faceless YouTube short optimized for retention."

            full_prompt = f"{system_rules}\n\nSTRICT TOPIC TO FOCUS ON: {title}"
            
            safe_print("[SCRIPT] Calling Gemini API for script generation...")
            response = model.generate_content(full_prompt)
            if response and response.text:
                script_text = response.text.strip()
                safe_print("[SCRIPT] Successfully retrieved script from Gemini.")
            else:
                safe_print("[SCRIPT] Gemini returned empty response. Using fallback.")
                script_text = get_fallback_script(title)
        
        except ImportError:
            safe_print("⚠️ [SCRIPT] google-generativeai module not installed. Falling back.")
            script_text = get_fallback_script(title)
        except Exception as e:
            safe_print(f"⚠️ [SCRIPT] Gemini API error: {e}. Falling back.")
            script_text = get_fallback_script(title)
    else:
        safe_print("⚠️ [SCRIPT] GEMINI_API_KEY not found in environment. Using fallback.")
        script_text = get_fallback_script(title)

    os.makedirs("scripts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_file = f"scripts/script_{timestamp}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    safe_print(f"[SUCCESS] Script saved to {script_file}")
    
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
