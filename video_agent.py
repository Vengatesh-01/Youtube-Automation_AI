"""
video_agent.py — Assembles final video using FFmpeg.
Concatenates SD-generated scene segments with a voiceover audio track.
"""

import os
import subprocess
import time
from utils import safe_print as log_agent


def _get_ffmpeg():
    """Resolve ffmpeg binary path — works on both Windows (local) and Linux (Render)."""
    candidates = [
        "ffmpeg",                           # system PATH (Linux/Render)
        r"C:\ffmpeg\bin\ffmpeg.exe",        # common Windows install
    ]
    for path in candidates:
        if path == "ffmpeg":
            return "ffmpeg"    # trust PATH on Linux
        if os.path.exists(path):
            return path
    return "ffmpeg"             # final fallback


def create_video(*args, **kwargs):
    """
    Assemble a final MP4 from scene video segments + optional voiceover.
    Supports signatures:
      create_video(video_segments, voice_file, output_path)
      create_video(script_file, voice_file, title, video_segments)
    """
    log_agent("🎬 Assembling final video with FFmpeg...")

    voice_file = None
    video_segments = []
    output_video = f"outputs/final_{int(time.time())}.mp4"

    for arg in args:
        if isinstance(arg, list):
            video_segments = arg
        elif isinstance(arg, str):
            if arg.endswith((".wav", ".mp3")):
                voice_file = arg
            elif arg.endswith(".mp4"):
                output_video = arg

    if not video_segments:
        log_agent("⚠️ No video segments provided. Cannot assemble video.")
        return None

    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
    concat_file = f"outputs/concat_list_{int(time.time())}.txt"
    with open(concat_file, "w") as f:
        for seg in video_segments:
            f.write(f"file '{os.path.abspath(seg)}'\n")

    ffmpeg = _get_ffmpeg()
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", concat_file]

    if voice_file and os.path.exists(voice_file):
        cmd.extend(["-i", voice_file])

    cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    cmd.append(output_video)

    log_agent(f"Running: ffmpeg concat -> {output_video}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    # Cleanup temp concat list
    try:
        os.remove(concat_file)
    except Exception:
        pass

    if res.returncode == 0 and os.path.exists(output_video):
        log_agent(f"✅ Video assembled: {output_video}")
        return output_video
    else:
        log_agent(f"❌ FFmpeg failed: {res.stderr[-500:]}")
        return None


def generate_talking_head(audio_file, image_file, topic_title="Unknown"):
    """Stub — talking head generation is disabled in the cloud pipeline."""
    log_agent(f"[INFO] Talking head generation not available for: {topic_title}")
    return None
