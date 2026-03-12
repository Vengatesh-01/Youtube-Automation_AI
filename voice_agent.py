import os
import asyncio
import edge_tts
from datetime import datetime
from utils import safe_print

VOICE = "en-US-AndrewNeural"  # Professional energetic voice for educational shorts

async def _synthesize(text: str, output_file: str):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(output_file)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            safe_print(f"TTS attempt {attempt + 1} failed ({e}). Retrying in 2s...")
            await asyncio.sleep(2)

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

    safe_print("Generating voiceover with Edge TTS...")
    asyncio.run(_synthesize(speech_text, output_file))
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
