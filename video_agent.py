"""
video_agent.py — Assembles final video using FFmpeg.
Creates a 16:9 video with a static background image, audio track, and burnt-in subtitles.
"""

import os
import platform
import subprocess
import time
from utils import safe_print, get_ffmpeg

def get_ffmpeg_subtitle_path(path):
    """
    Return a path string safe for use inside FFmpeg filter_complex on Windows.
    FFmpeg subtitle filter requires:
      - Forward slashes
      - Escaped colon after drive letter (C: → C\\:)
    """
    abs_path = os.path.abspath(path).replace('\\', '/')
    if platform.system() == 'Windows':
        # Escape the drive letter colon: C:/path → C\:/path
        if len(abs_path) > 1 and abs_path[1] == ':':
            abs_path = abs_path[0] + '\\:' + abs_path[2:]
    return abs_path

def assemble_podcast_video(background_image, final_audio, subtitle_file, output_video, video_type="long"):
    """
    Assemble the final MP4.
    video_type: "long" (16:9) or "short" (9:16)
    """
    safe_print(f"🎬 Assembling final {video_type} podcast video with FFmpeg...")
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

    ffmpeg = get_ffmpeg()

    # Get Windows-safe absolute path for subtitle filter
    sub_safe = get_ffmpeg_subtitle_path(subtitle_file)
    
    if video_type == "short":
        # No subtitles for shorts
        # [0:v] scale and crop background to 1080x1920
        # [1:a] generate waveform (cyan, centered line, 400x100 size for narrow screen)
        # [bg][wave] overlay waveform at the bottom center
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg]; "
            "[1:a]showwaves=s=400x120:mode=cline:colors=cyan[wave]; "
            "[bg][wave]overlay=(W-w)/2:H-h-200[outv]"
        )
    else:
        # 16:9 aspect ratio for long videos
        filter_complex = (
            "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[bg]; "
            "[1:a]showwaves=s=600x150:mode=cline:colors=cyan[wave]; "
            "[bg][wave]overlay=(W-w)/2:H-h-150[v_over]; "
            f"[v_over]subtitles='{sub_safe}':force_style='Fontname=Arial Bold,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=0,Alignment=2,MarginV=50'[outv]"
        )

    cmd = [
        ffmpeg, "-y", "-nostdin",
        "-loop", "1", "-i", background_image,
        "-i", final_audio,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", 
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
