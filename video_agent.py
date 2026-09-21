"""
video_agent.py — Assembles final video using FFmpeg.
Creates a 16:9 video with a static background image, audio track, and burnt-in subtitles.
"""

import os
import subprocess
import time
from utils import safe_print, get_ffmpeg

def assemble_podcast_video(background_image, final_audio, subtitle_file, output_video, video_type="long"):
    """
    Assemble the final MP4.
    video_type: "long" (16:9) or "short" (9:16)
    """
    safe_print(f"🎬 Assembling final {video_type} podcast video with FFmpeg...")
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

    ffmpeg = get_ffmpeg()

    # Convert paths to relative or forward-slashes for the subtitles filter
    sub_rel = os.path.relpath(subtitle_file).replace('\\', '/')
    
    if video_type == "short":
        # 9:16 aspect ratio for shorts
        # [0:v] scale and crop background to 1080x1920
        # [1:a] generate waveform (cyan, centered line, 400x100 size for narrow screen)
        # [bg][wave] overlay waveform at the bottom center
        # [v_over] add subtitles (Middle center Alignment=5, or Top Center Alignment=8 with large margin)
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg]; "
            "[1:a]showwaves=s=400x120:mode=cline:colors=cyan[wave]; "
            "[bg][wave]overlay=(W-w)/2:H-h-200[v_over]; "
            f"[v_over]subtitles='{sub_rel}':force_style='Fontname=Arial,Fontsize=65,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=8,MarginV=250'[outv]"
        )
    else:
        # 16:9 aspect ratio for long videos
        filter_complex = (
            "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[bg]; "
            "[1:a]showwaves=s=600x150:mode=cline:colors=cyan[wave]; "
            "[bg][wave]overlay=(W-w)/2:H-h-150[v_over]; "
            f"[v_over]subtitles='{sub_rel}':force_style='Fontname=Arial,Fontsize=55,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=8,MarginV=60'[outv]"
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
