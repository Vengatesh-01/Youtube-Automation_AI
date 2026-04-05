import os
import subprocess
import shutil
import time
from datetime import datetime
from utils import safe_print

def log_agent(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [VideoAgent-SadTalker] {msg}"
    safe_print(log_line)
    os.makedirs("videos", exist_ok=True)
    with open("videos/automation.log", "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

# Path configuration for Render (Linux)
SADTALKER_DIR = "/app/SadTalker"
SADTALKER_PYTHON = "python3" # Using the system python inside Docker
SADTALKER_INFER = os.path.join(SADTALKER_DIR, "inference.py")

# Fixed Assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXED_BG = os.path.join(BASE_DIR, "inputs", "fixed_bg.png")
FIXED_PORTRAIT = os.path.join(BASE_DIR, "inputs", "portrait.png")
FIXED_BGM = os.path.join(BASE_DIR, "assets", "bg_music.mp3")

def create_video(script_path: str, voice_file: str, topic_title: str = "Podcast", video_segments: list = [], background_video: str = "") -> str:
    """
    Generates a lip-synced video using SadTalker and composites it onto a fixed background.
    """
    log_agent(f"🚀 Starting SadTalker Pipeline for: {topic_title}")
    
    # 1. Prepare Work Directory
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = os.path.abspath(f"outputs/sad_{ts}")
    os.makedirs(work_dir, exist_ok=True)
    
    # 2. Run SadTalker
    log_agent("🎭 Running SadTalker Lip-Sync (Inference)...")
    # Using 256px mode for speed on CPU
    cmd = [
         SADTALKER_PYTHON, SADTALKER_INFER,
         "--driven_audio", os.path.abspath(voice_file),
         "--source_image", FIXED_PORTRAIT,
         "--result_dir", work_dir,
         "--cpu", 
         "--still", 
         "--preprocess", "full", 
         "--size", "256",
         "--enhancer", "None" # Enhancer is too slow on CPU
    ]
    
    try:
        process = subprocess.run(cmd, cwd=SADTALKER_DIR, capture_output=True, text=True, timeout=1200) # 20 mins timeout
        if process.returncode != 0:
            log_agent(f"❌ SadTalker failed: {process.stderr[-500:]}")
            return ""
    except Exception as e:
        log_agent(f"❌ SadTalker execution error: {e}")
        return ""

    # Find the generated video
    import glob
    vids = glob.glob(os.path.join(work_dir, "**", "*.mp4"), recursive=True)
    if not vids:
        log_agent("❌ No video produced by SadTalker.")
        return ""
    
    raw_face_vid = vids[0]
    log_agent(f"✅ Lip-sync face generated: {raw_face_vid}")

    # 3. Final Compositing with Background and Music (Using MoviePy)
    output_filename = f"podcast_{ts}.mp4"
    final_output = os.path.abspath(os.path.join("videos", output_filename))
    
    try:
        from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip
        
        log_agent("🎬 Compositing final video with Fixed Background...")
        
        # Load face video
        face_clip = VideoFileClip(raw_face_vid)
        duration = face_clip.duration
        
        # Load background
        bg_clip = ImageClip(FIXED_BG).set_duration(duration).resize(height=1920) # Portrait 9:16
        
        # Position face on top of background
        # SadTalker 256px usually needs scaling
        face_clip = face_clip.resize(width=800).set_position(("center", "center"))
        
        # Combine
        video = CompositeVideoClip([bg_clip, face_clip])
        
        # Add BGM
        if os.path.exists(FIXED_BGM):
            bgm = AudioFileClip(FIXED_BGM).volumex(0.15).set_duration(duration)
            original_audio = face_clip.audio.volumex(1.5)
            from moviepy.editor import CompositeAudioClip
            video.audio = CompositeAudioClip([original_audio, bgm])
        
        # Write output
        video.write_videofile(final_output, codec="libx264", audio_codec="aac", fps=24, logger=None)
        
        log_agent(f"🚀 SUCCESS! Video saved to: {final_output}")
        return final_output
        
    except Exception as e:
        log_agent(f"❌ Compositing failed: {e}")
        # Fallback: copy the raw face video if compositing fails
        shutil.copy(raw_face_vid, final_output)
        return final_output

if __name__ == "__main__":
    # Test call
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2])
