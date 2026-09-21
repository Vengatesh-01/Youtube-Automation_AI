"""
video_agent.py — Assembles final video using FFmpeg.
Creates a 16:9 video with a static background image, audio track, and burnt-in subtitles.
"""

import os
import subprocess
import time
from utils import safe_print, get_ffmpeg

def assemble_podcast_video(background_image, final_audio, subtitle_file, output_video):
    """
    Assemble the final MP4.
    """
    safe_print("🎬 Assembling final podcast video with FFmpeg...")
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

    ffmpeg = get_ffmpeg()

    # Convert paths to relative or forward-slashes for the subtitles filter
    # FFmpeg subtitles filter on Windows is notoriously picky about paths.
    # It's safest to use relative paths.
    sub_rel = os.path.relpath(subtitle_file).replace('\\', '/')
    
    # We want a 16:9 1920x1080 video. 
    # scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080
    # ensures it covers the screen without stretching.
    
    vf_filter = f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,subtitles='{sub_rel}'"

    cmd = [
        ffmpeg, "-y", "-nostdin",
        "-loop", "1", "-i", background_image,
        "-i", final_audio,
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_video
    ]

    safe_print(f"Running FFmpeg: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600)
    except subprocess.TimeoutExpired:
        safe_print("❌ FFmpeg timed out after 600 seconds!")
        return None

    if res.returncode == 0 and os.path.exists(output_video):
        safe_print(f"✅ Video assembled: {output_video}")
        return output_video
    else:
        stderr_text = res.stderr.decode('utf-8', errors='replace')[-1000:] if res.stderr else "No stderr"
        safe_print(f"❌ FFmpeg failed: {stderr_text}")
        return None
