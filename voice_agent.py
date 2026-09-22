"""
voice_agent.py — Generates MP3 voiceovers using Edge TTS (cloud, works on Render/Linux).
"""

import os
import asyncio
from utils import safe_print
import edge_tts

async def _amain_edge_tts(text: str, output_file: str, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_voice(text: str, output_file: str, voice_name: str, max_retries: int = 3) -> bool:
    """
    Generate voiceover using native edge_tts python library.
    Returns True if successful, False otherwise.
    """
    import time
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    for attempt in range(1, max_retries + 1):
        try:
            # Run the async function synchronously with a strict timeout
            asyncio.run(asyncio.wait_for(_amain_edge_tts(text, output_file, voice_name), timeout=60.0))
            if os.path.exists(output_file):
                safe_print(f"[VOICE] Edge TTS success: {output_file}")
                return True
        except asyncio.TimeoutError:
            safe_print(f"[VOICE] Attempt {attempt} - Edge TTS timed out for voice {voice_name}!")
        except Exception as e:
            safe_print(f"[VOICE] Attempt {attempt} - Edge TTS exception: {e}")
            
        if attempt < max_retries:
            wait_time = attempt * 2  # Exponential-ish backoff: 2s, 4s, etc.
            safe_print(f"[VOICE] Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        generate_voice(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        safe_print("Usage: python voice_agent.py <text> <output_file> <voice_name>")
