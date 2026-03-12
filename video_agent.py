import os
import subprocess
import glob
import random
import re
import numpy as np
from datetime import datetime, timezone
import gc
import psutil
import requests
import urllib.parse
import threading
from utils import safe_print
import uuid
from blender_agent import generate_blender_video

def log_agent(msg):
    try:
        mem = psutil.virtual_memory().percent
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        log_line = f"[{timestamp}] [EliteVideoAgent] [RAM: {mem}%] {msg}"
        
        safe_print(log_line)
            
        os.makedirs("videos", exist_ok=True)
        with open("videos/automation.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except:
        pass

# Point to bundled FFmpeg binary in venv - MUST BE SET BEFORE MOVIEPY IMPORTS
FFMPEG_PATH = os.path.join("venv", "Lib", "site-packages", "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe")
if os.path.exists(FFMPEG_PATH):
    os.environ["MOVIEPY_FFMPEG_BINARY"] = os.path.abspath(FFMPEG_PATH)
    os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.abspath(FFMPEG_PATH)

from moviepy import (
    AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip, TextClip, ImageClip,
    concatenate_videoclips, vfx
)

ASSETS_DIR = "assets"
AVATARS_DIR = os.path.join(ASSETS_DIR, "avatars")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
OUTPUT_DIR = "videos"

if os.name == 'nt':
    FONT_PATH = "C:/Windows/Fonts/arial.ttf"
    FONT_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"
else:
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def extract_keywords(text):
    words = re.findall(r'\b\w{5,}\b', text.lower())
    stop_words = {'about', 'there', 'their', 'would', 'could', 'should', 'these', 'those', 'where', 'which', 'today', 'hello', 'welcome', 'everyone', 'subscribe'}
    keywords = [w for w in words if w not in stop_words]
    return list(dict.fromkeys(keywords))

# 9:16 Shorts Configuration
TARGET_RESOLUTION = (1080, 1920)

def extract_scenes(script_text):
    """
    Enhanced Scene Parser for Cinematic Director.
    Extracts Scene blocks, Emotions, Camera movements, and Actions.
    """
    # Mapping for different possible markers
    scene_map = {
        "Scene 1": "[HOOK]",
        "Scene 2": "[CURIOSITY]",
        "Scene 3": "[EXPLANATION]",
        "Scene 4": "[INSIGHT]",
        "Scene 5": "[ENDING]"
    }
    markers = ["[HOOK]", "[CURIOSITY]", "[EXPLANATION]", "[INSIGHT]", "[ENDING]"]
    scenes = {}
    current_marker = None
    
    # Split by common scene headers
    parts = re.split(r'(Scene\s+\d+:?|\[.*?\])', script_text, flags=re.IGNORECASE)
    
    for part in parts:
        part_strip = part.strip()
        if not part_strip: continue
        
        # Identify if this part is a header
        header_marker = None
        if part_strip in markers:
            header_marker = part_strip
        else:
            for scene_key, m_val in scene_map.items():
                if scene_key.lower() in part_strip.lower():
                    header_marker = m_val
                    break
        
        if header_marker:
            current_marker = header_marker
            if current_marker not in scenes:
                scenes[current_marker] = {
                    "text": "", 
                    "visual_prompt": "", 
                    "emotion": "Neutral", 
                    "camera": "STATIC", 
                    "action": "Idle"
                }
        elif current_marker:
            # Parse block content for specific cinematic keywords
            lines = part_strip.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Check for specific labels
                if line.lower().startswith("emotion:"):
                    scenes[current_marker]["emotion"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("camera:"):
                    scenes[current_marker]["camera"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("character action:") or line.lower().startswith("action:") or line.lower().startswith("character:"):
                    scenes[current_marker]["action"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("environment:"):
                    scenes[current_marker]["environment"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("subtitle:"):
                    scenes[current_marker]["text"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("narrative:"):
                    # The spoken dialogue
                    scenes[current_marker]["spoken_text"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("duration:"):
                    pass
                elif "|" in line:
                    # Support the old VISUAL | TEXT format too
                    v_match = re.search(r'VISUAL:\s*(.*?)(?=\||$)', line, re.I)
                    t_match = re.search(r'TEXT:\s*(.*?)$', line, re.I)
                    if v_match: scenes[current_marker]["visual_prompt"] += v_match.group(1).strip() + " "
                    if t_match: scenes[current_marker]["text"] += t_match.group(1).strip() + " "
                else:
                    # Generic content fallback
                    if len(line) > 5:
                        if not scenes[current_marker].get("spoken_text"):
                            scenes[current_marker]["spoken_text"] = line + " "
                        else:
                            scenes[current_marker]["text"] += line + " "

    # Cleanup: If no VISUAL prompt was explicitly set, use the text to derive one
    for s_id in scenes:
        if not scenes[s_id]["visual_prompt"]:
            scenes[s_id]["visual_prompt"] = f"{scenes[s_id]['action']} {scenes[s_id]['emotion']}"

    # Final fallback
    if not scenes and script_text.strip():
        scenes["[EXPLANATION]"] = {"text": script_text.strip()[:300], "visual_prompt": "Neutral Idle", "emotion": "Neutral", "camera": "STATIC"}
            
    return scenes

def add_audio_layers(video_clip, voice_file):
    log_agent("[AUDIO] Mixing Voiceover and Background Music")
    voice = AudioFileClip(voice_file)
    
    # Try to find background music
    music_files = glob.glob(os.path.join(MUSIC_DIR, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, "*.wav"))
    if music_files:
        try:
            bg_music_path = random.choice(music_files)
            bg_music = AudioFileClip(bg_music_path).with_volume_scaled(0.12)
            
            # Loop music if shorter than video
            if bg_music.duration < video_clip.duration:
                from moviepy.audio.fx.all import audio_loop
                bg_music = audio_loop(bg_music, duration=video_clip.duration)
            else:
                bg_music = bg_music.subclip(0, video_clip.duration)
                
            from moviepy import CompositeAudioClip
            final_audio = CompositeAudioClip([voice, bg_music])
        except Exception as e:
            log_agent(f"[AUDIO] Music mix failed: {e}. Using voice only.")
            final_audio = voice
    else:
        final_audio = voice
        
    return video_clip.with_audio(final_audio)

# --- Replaced 2D Image APIs with Blender Module ---
def get_audio_duration(file_path):
    """Fallback duration parser using FFmpeg directly."""
    try:
        # Resolve path to handle spaces and relative paths
        target = os.path.abspath(file_path)
        cmd = [FFMPEG_PATH, "-i", target]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stderr
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        pass
    return 10.0 # Default fallback

def create_video(script, voice_file: str, topic_title: str = "Viral Short") -> str:
    log_agent(f"[INIT] Offline Blender Engine: {topic_title}")
    
    if isinstance(script, str) and os.path.isfile(script):
        with open(script, "r", encoding="utf-8") as f:
            script_text = f.read()
    else:
        script_text = str(script)
        
    scene_defs = extract_scenes(script_text)
    total_duration = get_audio_duration(voice_file)
    log_agent(f"[AUDIO] Total duration: {total_duration}s")

    # ---------------------------------------------------------
    # NEW BLENDER OFFLINE PIPELINE
    # ---------------------------------------------------------
    log_agent("[BLENDER] Handing off to Blender Agent for 3D Video Generation...")
    
    os.makedirs(os.path.join(ASSETS_DIR, "ai_scenes"), exist_ok=True)
    blender_out_path = os.path.join(ASSETS_DIR, "ai_scenes", f"blender_base_{uuid.uuid4().hex[:8]}.mp4")
    
    success = generate_blender_video(scene_defs, voice_file, blender_out_path)
    
    if not success or not os.path.exists(blender_out_path):
        log_agent("[BLENDER] Blender generation failed. Generating emergency color clip fallback.")
        final_video = ColorClip(size=TARGET_RESOLUTION, color=(20, 20, 30), duration=total_duration)
    else:
        # Load the rendered video from Blender
        final_video = VideoFileClip(blender_out_path)
        
        # In case the rendered video is slightly shorter/longer than the audio, conform it
        if final_video.duration < total_duration:
            # Loop it just in case
            final_video = final_video.with_duration(total_duration) # Moviepy 2 style
        else:
            final_video = final_video.subclipped(0, total_duration)
    
    # --- Weighted Subtitle Timing --- 
    # Each chunk's duration is proportional to its word count, so longer phrases
    # stay on screen longer and shorter ones flash quickly. Much more readable.
    log_agent("[SUBTITLES] Generating Weighted Timed Captions")
    clean_text = re.sub(r'\[.*?\]', '', script_text)
    clean_text = re.sub(r'\|\s*(VISUAL|TEXT|POSE):.*?(?=\||$)', '', clean_text)
    words = clean_text.split()

    chunk_size = 3  # 3 words per frame — more readable, less frantic
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    total_words = sum(len(c.split()) for c in chunks)

    # Build weighted durations so each chunk's screen time is proportional to its length
    weighted_durations = []
    for chunk in chunks:
        word_count = len(chunk.split())
        weight = word_count / max(total_words, 1)
        weighted_durations.append(weight * total_duration)

    caption_clips = []
    current_start = 0.0
    for idx, chunk_text in enumerate(chunks):
        c_dur = weighted_durations[idx]
        # Clamp: each subtitle shows for at least 0.4s
        c_dur = max(c_dur, 0.4)
        try:
            # Modern Bold Style - Clean and Balanced
            cp = TextClip(
                text=chunk_text.upper(),
                font_size=88,
                color="white",
                stroke_color="black",
                stroke_width=2,
                font=FONT_BOLD_PATH,
                method="caption",
                size=(940, None),
                text_align="center"
            ).with_start(current_start).with_duration(c_dur).with_position(("center", 1400))

            # Smooth Cinematic Entry (Fade-in + Elastic Pop)
            def cinematic_entry(dur):
                def anim(t):
                    # Scale bounce logic
                    scale = 1.0
                    if t < 0.1: scale = 0.5 + 5.0 * t
                    elif t < 0.2: scale = 1.0 + 0.2 * (1.0 - (t - 0.1)/0.1)
                    return scale
                return anim

            # Apply Fade + Resize
            cp = cp.with_effects([
                vfx.FadeIn(0.15),
                vfx.Resize(cinematic_entry(c_dur))
            ])
            
            caption_clips.append(cp)
            current_start += c_dur
        except Exception as e:
            log_agent(f"⚠️ [SUBTITLES] Clip error: {e}")
            current_start += c_dur
            
    final_video = CompositeVideoClip([final_video] + caption_clips)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    temp_no_audio = os.path.join(OUTPUT_DIR, f"temp_no_audio_{ts}.mp4")
    out_file = os.path.join(OUTPUT_DIR, f"pixar_short_{ts}.mp4")
    
    # 1. Export Visuals Only (MoviePy is stable for video-only)
    log_agent("[VIDEO] Rendering visual layers (subtitles)...")
    final_video.write_videofile(temp_no_audio, fps=30, codec="libx264", audio=False, logger="bar", preset="ultrafast")
    
    # 2. Merge Audio using robust FFmpeg Subprocess (SPACE-FREE PATH STRATEGY)
    log_agent("[AUDIO] Fusing audio layers via space-free temp path...")
    
    import shutil
    temp_fusion_dir = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"video_fusion_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_fusion_dir, exist_ok=True)
    
    # 1. Copy to temp dir (avoiding workspace spaces)
    safe_video = os.path.join(temp_fusion_dir, "input_video.mp4")
    safe_audio = os.path.join(temp_fusion_dir, "input_audio.mp3")
    safe_out = os.path.join(temp_fusion_dir, "output_fused.mp4")
    
    try:
        shutil.copy2(temp_no_audio, safe_video)
        shutil.copy2(voice_file, safe_audio)
        
        merge_cmd = [
            FFMPEG_PATH, "-y",
            "-i", safe_video,
            "-i", safe_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            safe_out
        ]
        
        log_agent(f"[FFMPEG] Fusing in {temp_fusion_dir}...")
        subprocess.run(merge_cmd, check=True, capture_output=True, text=True)
        
        # 2. Copy back to final destination
        shutil.copy2(safe_out, out_file)
        log_agent(f"[SUCCESS] Final video fused and moved: {out_file}")
        
    except Exception as e:
        log_agent(f"[ERROR] Fusion strategy failed: {e}")
        # Fallback
        if os.path.exists(temp_no_audio):
             os.rename(temp_no_audio, out_file)
    finally:
        # Cleanup space-free temp dir
        shutil.rmtree(temp_fusion_dir, ignore_errors=True)

    # Cleanup
    final_video.close()
    if os.path.exists(temp_no_audio) and out_file != temp_no_audio:
        os.remove(temp_no_audio)
    
    gc.collect()
    return out_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Viral Short")
