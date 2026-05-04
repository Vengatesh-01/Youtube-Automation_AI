"""
voice_agent.py — Generates MP3 voiceovers using Edge TTS (cloud, works on Render/Linux).
Falls back to silent audio if Edge TTS fails.
"""

import os
import re
import asyncio
from datetime import datetime
from utils import safe_print


VOICE = "en-US-ChristopherNeural"   # Change to "en-US-JennyNeural" for female


async def _synthesize_edge_tts(text: str, output_file: str) -> bool:
    """Generate voiceover using Microsoft Edge TTS (no API key required)."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_file)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            safe_print(f"[VOICE] Edge TTS success: {output_file}")
            return True
        return False
    except Exception as e:
        safe_print(f"[VOICE] Edge TTS failed: {e}")
        return False


def _synthesize_silence(output_file: str, duration: int = 30) -> bool:
    """Generate a silent audio file via FFmpeg as last-resort fallback."""
    try:
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=mono",
            "-t", str(duration),
            "-q:a", "9",
            "-acodec", "libmp3lame",
            output_file
        ]
        res = subprocess.run(cmd, capture_output=True)
        return res.returncode == 0
    except Exception as e:
        safe_print(f"[VOICE] Silence fallback failed: {e}")
        return False


def _extract_speech_text(script_text: str) -> str:
    """Pull only the Voiceover lines from a formatted script."""
    voiceover_lines = re.findall(r'Voiceover:\s*(.*)', script_text, re.IGNORECASE)
    if voiceover_lines:
        return ' '.join(voiceover_lines)
    # Fallback: strip formatting tags and return clean text
    text = re.sub(r'(?i)Image Prompt:.*', '', script_text)
    text = re.sub(r'(?i)Text:.*', '', text)
    text = re.sub(r'(?i)Duration:.*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()


def generate_voice(script) -> str:
    """
    Generate a voiceover MP3 from a script.
    Accepts either a file path (str) to a .txt script, or raw script text.
    Returns the path to the saved MP3 file, or None on failure.
    """
    # Read from file if a path was passed
    if isinstance(script, str) and os.path.isfile(script):
        with open(script, "r", encoding="utf-8") as f:
            script_text = f.read()
        safe_print(f"[VOICE] Reading script from {script}")
    else:
        script_text = str(script)
        safe_print("[VOICE] Using provided script text.")

    speech_text = _extract_speech_text(script_text)
    if not speech_text:
        safe_print("[VOICE] Warning: No speech text extracted from script.")
        speech_text = "Welcome to today's video."

    os.makedirs("voiceovers", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"voiceovers/voiceover_{timestamp}.mp3"

    # Primary: Edge TTS
    safe_print("[VOICE] Generating voiceover with Edge TTS...")
    success = asyncio.run(_synthesize_edge_tts(speech_text, output_file))

    # Fallback: silent audio
    if not success:
        safe_print("[VOICE] Falling back to silent audio placeholder...")
        success = _synthesize_silence(output_file)

    if not success:
        safe_print("[VOICE] ERROR: All voice generation methods failed.")
        return None

    safe_print(f"[VOICE] Voiceover saved: {output_file}")
    return output_file


# Backward-compatible alias
generate_voiceover = generate_voice


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_voice(sys.argv[1])
    else:
        safe_print("Usage: python voice_agent.py <path_to_script.txt>")
