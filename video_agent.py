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

def log_agent(msg):
    try:
        mem = psutil.virtual_memory().percent
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        log_line = f"[{timestamp}] [EliteVideoAgent] [RAM: {mem}%] {msg}"
        print(log_line, flush=True)
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

def draw_stick_figure(output_path, pose="Standing", overlay_text=""):
    """Fallback: Draw stick figure if API fails."""
    from PIL import Image, ImageDraw, ImageFont
    import math
    import random
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2 + 100
    draw.ellipse([cx - 90, cy - 180, cx + 90, cy], outline="black", width=10)
    draw.line([cx, cy, cx, cy + 300], fill="black", width=12)
    img.save(output_path)
    return True

def generate_pollinations_image(prompt, output_path, timeout=120):
    """Prioritize high-quality Pixar 3D generation with Robust Retries and Model Switching."""
    import time
    import random
    
    # Dynamic pose integration: ensure prompt reflects the action requested
    action_cue = prompt if "character" in prompt.lower() else f"character {prompt}"
    enhanced_prompt = (
        f"3D Pixar Disney style animation, high-quality 3D render, {action_cue}, "
        "expressive face with a little smile, eyes blinking and moving, "
        "subsurface scattering, warm volumetric lighting, soft shadows, "
        "vibrant colors, highly detailed textures, 8k, cinematic composition, 9:16 aspect ratio"
    )
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # Model rotation strategy to handle 500 errors gracefully
    models = ["flux", "turbo", "unity"]
    max_retries = 1 # Quick fail-fast to ensure rapid video generation
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for attempt in range(max_retries):
        # Rotate through models: flux -> turbo -> unity -> flux ...
        current_model = models[attempt % len(models)]
        wait_time = (attempt + 1) * 10 # Simple incremental backoff
        
        log_agent(f"🎨 [API] Requesting Pixar 3D (Attempt {attempt+1}/{max_retries}, Model: {current_model})...")
        try:
            current_seed = random.randint(1, 9999999)
            current_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&seed={current_seed}&model={current_model}&nologo=true"
            
            response = requests.get(current_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                if len(response.content) < 5000: # Sanit check - empty or corrupt-looking file
                     log_agent(f"⚠️ [API] Response too small ({len(response.content)} bytes). Retrying...")
                     time.sleep(5)
                     continue
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                log_agent(f"✅ [API] Success! Pixar 3D asset generated using {current_model}.")
                return True
            elif response.status_code == 429:
                delay = 45 + (attempt * 5)
                log_agent(f"⚠️ [API] Rate limited. Waiting {delay}s...")
                time.sleep(delay)
            elif response.status_code == 500:
                log_agent(f"⚠️ [API] Server Error 500 on model '{current_model}'. Switching model and retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                log_agent(f"⚠️ [API] Unexpected Status {response.status_code}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        except requests.exceptions.Timeout:
            log_agent(f"⚠️ [API] Request Timeout. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            log_agent(f"⚠️ [API] Attempt {attempt+1} failed: {str(e)}")
            time.sleep(wait_time)
            
    return False

def get_shorts_visual(scene_label, duration, topic_title, scene_data, img_path=None):
    """Create Pixar-style 3D visuals with dynamic 'Slow Zoom' — Optimized for Consistency."""
    
    if not img_path or not os.path.exists(img_path):
        visual_prompt = scene_data.get("visual_prompt", topic_title)
        os.makedirs(os.path.join(ASSETS_DIR, "ai_scenes"), exist_ok=True)
        ts = datetime.now().strftime("%H%M%S%f")
        img_path = os.path.join(ASSETS_DIR, "ai_scenes", f"pixar_{ts}.png")
        
        import time
        time.sleep(3.5) # Critical cool-down for Pollinations Rate Limits
        
        success = generate_pollinations_image(visual_prompt, img_path, timeout=60)
        if not success:
            log_agent("🔄 [FALLBACK] API Failed, using stick figure")
            draw_stick_figure(img_path)
    
    if os.path.exists(img_path):
        bg = ImageClip(img_path).with_duration(duration)
        
        # Smooth Ken Burns (Slow Zoom)
        # We alternate zoom types to keep it dynamic like Excuse Erased
        zoom_type = "in" if hash(img_path) % 2 == 0 else "out"
        def zoom_effect(t):
            if zoom_type == "in":
                return 1.0 + 0.20 * (t / duration)
            else:
                return 1.20 - 0.20 * (t / duration)
        
        # Robust cover resizing to avoid black bars
        w, h = bg.size
        ratio = h / float(w)
        target_ratio = 1920 / 1080.0
        
        if ratio > target_ratio: # Image is taller than target
            bg = bg.resized(width=1080)
        else: # Image is wider than target
            bg = bg.resized(height=1920)
            
        bg = bg.with_effects([vfx.Resize(zoom_effect)])
        bg = bg.with_position(("center", "center"))
        return bg
    else:
        return ColorClip(size=TARGET_RESOLUTION, color=(255, 255, 255), duration=duration)

def add_audio_layers(video_clip, voice_file):
    audio = AudioFileClip(voice_file)
    from moviepy import CompositeAudioClip
    music_files = glob.glob(os.path.join(MUSIC_DIR, "*.mp3"))
    if music_files:
        chosen = random.choice(music_files)
        music = AudioFileClip(chosen).with_duration(video_clip.duration).multiply_volume(0.12)
        final_audio = CompositeAudioClip([audio, music])
        return video_clip.with_audio(final_audio)
    return video_clip.with_audio(audio)

def create_video(script, voice_file: str, topic_title: str = "Viral Short") -> str:
    log_agent(f"🚀 [INIT] Pixar 3D Engine: {topic_title}")
    
    if isinstance(script, str) and os.path.isfile(script):
        with open(script, "r", encoding="utf-8") as f:
            script_text = f.read()
    else:
        script_text = str(script)
        
    scene_defs = extract_scenes(script_text)
    temp_audio = AudioFileClip(voice_file)
    total_duration = temp_audio.duration
    
    timing = {"[HOOK]": 0.08, "[CURIOSITY]": 0.22, "[EXPLANATION]": 0.35, "[INSIGHT]": 0.25, "[ENDING]": 0.10}
    
    scenes = []
    current_time = 0
    for label, content in scene_defs.items():
        dur = timing.get(label, 0.2) * total_duration
        
        # PRIORITIZE Premium Pre-generated Pixar visuals if they exist
        os.makedirs(os.path.join(ASSETS_DIR, "ai_scenes"), exist_ok=True)
        visual_prompt = content.get("visual_prompt", topic_title)
        scene_img_path = os.path.join(ASSETS_DIR, "ai_scenes", f"scene_{label[1:-1]}.png")
        
        if not os.path.exists(scene_img_path):
            ts = datetime.now().strftime("%H%M%S%f")
            scene_img_path = os.path.join(ASSETS_DIR, "ai_scenes", f"temp_{label[1:-1]}_{ts}.png")
            
            import time
            time.sleep(30.0) # Absolute stability for Rate Limits (1 scene per 30s)
            log_agent(f"🎨 [SCENE] Rendering 3D Pixar Visual for {label}...")
            
            success = generate_pollinations_image(visual_prompt, scene_img_path, timeout=90)
            if not success:
                draw_stick_figure(scene_img_path)
        else:
            log_agent(f"💎 [SCENE] Using PREMIUM pre-generated visual for {label}")
            
        # Split into small clips for memory safety, but reuse the image
        chunk_dur = 2.5
        num_chunks = max(1, int(dur / chunk_dur))
        actual_chunk_dur = dur / num_chunks
        
        for _ in range(num_chunks):
            clip = get_shorts_visual(label, actual_chunk_dur, topic_title, content, img_path=scene_img_path)
            clip = clip.with_effects([vfx.FadeIn(0.2)])
            scenes.append(clip)
            
        current_time += dur
        gc.collect()
            
    final_video = concatenate_videoclips(scenes, method="chain")
    
    # Subtitles - EXCUSE ERASER STYLE (High Contrast White on Black Stroke)
    log_agent("🎬 [SUBTITLES] Generating Bold Pro Captions")
    clean_text = re.sub(r'\[.*?\]', '', script_text)
    clean_text = re.sub(r'\|\s*(VISUAL|TEXT|POSE):.*?(?=\||$)', '', clean_text)
    words = clean_text.split()
    
    chunk_size = 2 # 2 words per screen is faster and more viral
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    c_dur = total_duration / max(len(chunks), 1)
    
    caption_clips = []
    for idx, chunk_text in enumerate(chunks):
        try:
            cp = TextClip(
                text=chunk_text.upper(), 
                font_size=90, 
                color="white", # PURE WHITE TEXT
                stroke_color="black", # THICK BLACK OUTLINE
                stroke_width=6, 
                font=FONT_BOLD_PATH,
                method="caption", 
                size=(950, None), 
                text_align="center"
            ).with_start(idx * c_dur).with_duration(c_dur).with_position(("center", 1150)) # slightly below center for visibility
            
            # Pop Effect
            def pop_animation(t):
                if t < 0.08: return 0.6 + 8 * t
                if t < 0.2: return 1.2 - 2 * (t - 0.08)
                return 1.0
            
            cp = cp.with_effects([vfx.Resize(pop_animation)])
            caption_clips.append(cp)
        except Exception:
            pass
            
    final_video = CompositeVideoClip([final_video] + caption_clips)
    final_video = add_audio_layers(final_video, voice_file)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"pixar_short_{ts}.mp4")
    
    final_video.write_videofile(out_file, fps=30, codec="libx264", audio_codec="aac", logger=None, preset="ultrafast")
    
    final_video.close()
    temp_audio.close()
    for scene in scenes: scene.close()
    gc.collect()
    
    return out_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Viral Short")
