import os
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
    """Parse the script into 5 defined scenes based on markers ([HOOK] or Scene 1:), extracting visuals and text."""
    # Mapping for new format to old timing markers
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
    
    # Split by either [MARKER] or Scene X: (with optional colon/newlines)
    parts = re.split(r'(\[.*?\]|Scene\s+\d+:?)', script_text, flags=re.IGNORECASE)
    
    for part in parts:
        part_strip = part.strip()
        
        # Check if it's a marker
        mapped_marker = None
        if part_strip in markers:
            mapped_marker = part_strip
        else:
            # Check for Scene X format
            for scene_key, m_val in scene_map.items():
                if scene_key.lower() in part_strip.lower():
                    mapped_marker = m_val
                    break
        
        if mapped_marker:
            current_marker = mapped_marker
            if current_marker not in scenes:
                scenes[current_marker] = {"text": "", "visual_prompt": "3D Pixar style character", "overlay_text": ""}
        elif current_marker:
            # Look for VISUAL and TEXT markers in the content
            visual_match = re.search(r'\|\s*VISUAL:\s*(.*?)\s*(?=\||$)', part)
            text_match = re.search(r'\|\s*TEXT:\s*(.*?)(?=$|\|)', part)
            
            if visual_match:
                scenes[current_marker]["visual_prompt"] = visual_match.group(1).strip()
            
            # Combine clean content for text
            clean_content = re.sub(r'\|\s*VISUAL:.*?(?=\||$)', '', part)
            clean_content = re.sub(r'\|\s*TEXT:.*?(?=$|\|)', '', clean_content).strip()
            
            if clean_content:
                scenes[current_marker]["text"] += clean_content + " "
            if text_match:
                scenes[current_marker]["overlay_text"] = text_match.group(1).strip()
            
    # Final cleanup: ensure we have something to render
    if not scenes and script_text.strip():
        # Last resort: just treat the whole thing as one scene
        scenes["[EXPLANATION]"] = {"text": script_text.strip()[:200], "visual_prompt": "3D Pixar style character", "overlay_text": ""}
            
    return scenes

def add_audio_layers(video_clip, voice_file):
    log_agent("🎵 [AUDIO] Mixing Voiceover and Background Music")
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
            log_agent(f"⚠️ [AUDIO] Music mix failed: {e}. Using voice only.")
            final_audio = voice
    else:
        final_audio = voice
        
    return video_clip.with_audio(final_audio)

# --- Replaced 2D Image APIs with Blender Module ---
from blender_agent import generate_blender_video
import uuid

def create_video(script, voice_file: str, topic_title: str = "Viral Short") -> str:
    log_agent(f"🚀 [INIT] Offline Blender Engine: {topic_title}")
    
    if isinstance(script, str) and os.path.isfile(script):
        with open(script, "r", encoding="utf-8") as f:
            script_text = f.read()
    else:
        script_text = str(script)
        
    scene_defs = extract_scenes(script_text)
    temp_audio = AudioFileClip(voice_file)
    total_duration = temp_audio.duration

    # ---------------------------------------------------------
    # NEW BLENDER OFFLINE PIPELINE
    # ---------------------------------------------------------
    log_agent("🎬 [BLENDER] Handing off to Blender Agent for 3D Video Generation...")
    
    os.makedirs(os.path.join(ASSETS_DIR, "ai_scenes"), exist_ok=True)
    blender_out_path = os.path.join(ASSETS_DIR, "ai_scenes", f"blender_base_{uuid.uuid4().hex[:8]}.mp4")
    
    success = generate_blender_video(scene_defs, voice_file, blender_out_path)
    
    if not success or not os.path.exists(blender_out_path):
        log_agent("⚠️ [BLENDER] Blender generation failed. Generating emergency color clip fallback.")
        final_video = ColorClip(size=TARGET_RESOLUTION, color=(20, 20, 30), duration=total_duration)
    else:
        # Load the rendered video from Blender
        final_video = VideoFileClip(blender_out_path)
        
        # In case the rendered video is slightly shorter/longer than the audio, conform it
        if final_video.duration < total_duration:
            # Loop it just in case
            from moviepy.video.fx.all import loop
            final_video = loop(final_video, duration=total_duration)
        else:
            final_video = final_video.subclip(0, total_duration)
    
    # --- Weighted Subtitle Timing --- 
    # Each chunk's duration is proportional to its word count, so longer phrases
    # stay on screen longer and shorter ones flash quickly. Much more readable.
    log_agent("🎬 [SUBTITLES] Generating Weighted Timed Captions")
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
            cp = TextClip(
                text=chunk_text.upper(),
                font_size=88,
                color="white",
                stroke_color="black",
                stroke_width=3,  # Reduced from 6 → cleaner letters, no artifact bleed
                font=FONT_BOLD_PATH,
                method="caption",
                size=(940, None),
                text_align="center"
            ).with_start(current_start).with_duration(c_dur).with_position(("center", 1150))

            # Pop-in bounce effect
            def make_pop(dur):
                def pop_animation(t):
                    if t < 0.07: return 0.65 + 5 * t
                    if t < 0.18: return 1.15 - 1.5 * (t - 0.07)
                    return 1.0
                return pop_animation

            cp = cp.with_effects([vfx.Resize(make_pop(c_dur))])
            caption_clips.append(cp)
            current_start += c_dur
        except Exception:
            current_start += c_dur
            
    final_video = CompositeVideoClip([final_video] + caption_clips)
    final_video = add_audio_layers(final_video, voice_file)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"pixar_short_{ts}.mp4")
    
    final_video.write_videofile(out_file, fps=30, codec="libx264", audio_codec="aac", logger=None, preset="ultrafast")
    
    final_video.close()
    temp_audio.close()
    gc.collect()
    
    return out_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Viral Short")
