"""
video_agent.py — Assembles final video using FFmpeg.
Concatenates SD-generated scene segments with a voiceover audio track.
"""

import os
import subprocess
import time
from utils import safe_print as log_agent, get_ffmpeg





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

    ffmpeg = get_ffmpeg()
    cmd = [ffmpeg, "-y", "-nostdin", "-f", "concat", "-safe", "0", "-i", concat_file]

    if voice_file and os.path.exists(voice_file):
        cmd.extend(["-i", voice_file])

    cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    cmd.append(output_video)

    log_agent(f"Running: ffmpeg concat -> {output_video}")
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    except subprocess.TimeoutExpired:
        log_agent("❌ FFmpeg timed out after 300 seconds!")
        return None

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
