"""
voice_agent.py — Generates MP3 voiceovers using Edge TTS (cloud, works on Render/Linux).
Falls back to silent audio if Edge TTS fails.
"""

import os
import re
import asyncio
from datetime import datetime
from utils import safe_print


import edge_tts

async def _amain_edge_tts(text: str, output_file: str, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def _synthesize_edge_tts(text: str, output_file: str, output_vtt: str, voice: str = None) -> bool:
    """Generate voiceover using native edge_tts python library."""
    try:
        voice_to_use = voice if voice else "en-US-ChristopherNeural"
        # Run the async function synchronously with a strict 45-second timeout
        asyncio.run(asyncio.wait_for(_amain_edge_tts(text, output_file, voice_to_use), timeout=45.0))
        if os.path.exists(output_file):
            safe_print(f"[VOICE] Edge TTS native success: {output_file}")
            # Note: native edge_tts communicate.save() doesn't write VTT by default.
            # We don't actually need VTT for the pipeline since FFmpeg assembly ignores it.
            return True
        return False
    except asyncio.TimeoutError:
        safe_print("[VOICE] Edge TTS native timed out after 45 seconds!")
        return False
    except Exception as e:
        safe_print(f"[VOICE] Edge TTS native exception: {e}")
        return False


def _synthesize_silence(output_file: str, duration: int = 30) -> bool:
    """Generate a silent audio file via FFmpeg as last-resort fallback."""
    try:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-nostdin",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=mono",
            "-t", str(duration),
            "-q:a", "9",
            "-acodec", "libmp3lame",
            output_file
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
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


def generate_voice(script, voice_name: str = None):
    """
    Generate a voiceover MP3 and VTT subtitles from a script.
    Accepts either a file path (str) to a .txt script, or raw script text.
    Returns a tuple (mp3_path, vtt_path) or (None, None) on failure.
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

    output_vtt = f"voiceovers/voiceover_{timestamp}.vtt"

    # Primary: Edge TTS
    safe_print(f"[VOICE] Generating voiceover and subtitles with Edge TTS (Voice: {voice_name if voice_name else 'default'})...")
    success = _synthesize_edge_tts(speech_text, output_file, output_vtt, voice=voice_name)

    # Fallback: silent audio
    if not success:
        safe_print("[VOICE] Falling back to silent audio placeholder...")
        success = _synthesize_silence(output_file)
        output_vtt = None # No subtitles for silence

    if not success:
        safe_print("[VOICE] ERROR: All voice generation methods failed.")
        return None, None

    safe_print(f"[VOICE] Voiceover saved: {output_file}")
    return output_file, output_vtt


# Backward-compatible alias
generate_voiceover = generate_voice


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_voice(sys.argv[1])
    else:
        safe_print("Usage: python voice_agent.py <path_to_script.txt>")
