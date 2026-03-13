import os
import pyttsx3
from datetime import datetime
from utils import safe_print

def _synthesize(text: str, output_file: str):
    """Fallback fully offline TTS using pyttsx3"""
    try:
        engine = pyttsx3.init()
        # You can adjust properties if needed
        # engine.setProperty('rate', 150)    
        # engine.setProperty('volume', 0.9)  
        
        # Try to find a good female/male voice if installed
        voices = engine.getProperty('voices')
        for voice in voices:
            if "david" in voice.name.lower() or "zira" in voice.name.lower() or "andrew" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
                
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        return True
    except Exception as e:
        safe_print(f"Offline TTS failed: {e}")
        return False

def generate_voice(script) -> str:
    """
    Generate a voiceover MP3 from a script.
    Accepts either a file path (str) to a .txt script, or raw script text.
    Returns the path to the saved MP3 file.
    """
    # Accept file path or raw text
    if isinstance(script, str) and os.path.isfile(script):
        with open(script, "r", encoding="utf-8") as f:
            script_text = f.read()
        safe_print(f"Reading script from {script}")
    else:
        script_text = script
        safe_print("Using provided script text.")

    os.makedirs("voiceovers", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"voiceovers/voiceover_{timestamp}.mp3"

    import re
    speech_text = re.sub(r'\[.*?\]', '', script_text).strip()

    safe_print("Generating voiceover with Offline pyttsx3...")
    success = _synthesize(speech_text, output_file)
    if not success:
        safe_print("[ERROR] Could not generate voiceover.")
        return None
    safe_print(f"Voiceover saved to {output_file}")
    return output_file

# Backward-compatible alias
generate_voiceover = generate_voice

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_voice(sys.argv[1])
    else:
        safe_print("Usage: python voice_agent.py <path_to_script_txt>")
