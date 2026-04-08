import os
import subprocess
import time
from utils import safe_print as log_agent

def create_video(*args, **kwargs):
    """
    Unified FFmpeg-based proxy for create_video, replacing Blender.
    Supports signatures like:
      create_video(script_file, voice_file, title, video_segments)
      create_video(script_text, voice_file, output_video)
    """
    log_agent("🎬 Proxy create_video called: Reconstructing video using FFmpeg (Blender disabled).")
    
    # Heuristics to figure out args
    voice_file = None
    video_segments = []
    output_video = f"outputs/final_{int(time.time())}.mp4"
    
    for arg in args:
        if isinstance(arg, list):
            video_segments = arg
        elif isinstance(arg, str):
            if arg.endswith(".wav") or arg.endswith(".mp3"):
                voice_file = arg
            elif arg.endswith(".mp4"):
                output_video = arg

    if not video_segments:
        # Fallback to an empty or default transparent background video
        log_agent("⚠️ No video segments provided. Cannot assemble without background.")
        return None

    # Concatenate segments using FFmpeg concat protocol
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
    concat_file = f"outputs/concat_list_{int(time.time())}.txt"
    with open(concat_file, "w") as f:
        for seg in video_segments:
            f.write(f"file '{os.path.abspath(seg)}'\n")
            
    ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
    if not os.path.exists(ffmpeg):
        ffmpeg = r"C:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
    if not os.path.exists(ffmpeg):
        ffmpeg = "ffmpeg"
        
    cmd = [
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", concat_file
    ]
    if voice_file and os.path.exists(voice_file):
        cmd.extend(["-i", voice_file])
    cmd.extend([
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest"
    ])
    cmd.append(output_video)
    
    log_agent(f"Running FFmpeg concat: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(output_video):
        log_agent(f"✅ FFmpeg assembly success: {output_video}")
        return output_video
    else:
        log_agent(f"❌ FFmpeg assembly failed: {res.stderr}")
        return None

def generate_talking_head(audio_file, image_file, topic_title="Unknown"):
    log_agent(f"🚧 SadTalker is disabled. Skipping talking head generation for: {topic_title}")
    return None
