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

def use_premium_fallback(output_path):
    """Fallback: Use a high-quality pre-stored Pixar avatar if API fails."""
    import shutil
    log_agent("💎 [FALLBACK] Using PREMIUM asset from assets/avatars/...")
    
    avatar_assets = glob.glob(os.path.join(AVATARS_DIR, "*.png"))
    if not avatar_assets:
        # Final safety: draw stick figure if even assets are missing
        from PIL import Image, ImageDraw
        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        cx, cy = W // 2, H // 2 + 100
        draw.ellipse([cx - 90, cy - 180, cx + 90, cy], outline="black", width=10)
        draw.line([cx, cy, cx, cy + 300], fill="black", width=12)
        img.save(output_path)
        return True
    
    # Exclude small avatar icons, prefer the large ones like expert.png or learner.png
    large_assets = [a for a in avatar_assets if os.path.getsize(a) > 100000]
    chosen = random.choice(large_assets) if large_assets else random.choice(avatar_assets)
    
    try:
        shutil.copy(chosen, output_path)
        return True
    except:
        return False

def generate_pollinations_image(prompt, output_path, timeout=120):
    """Prioritize high-quality Pixar 3D generation with Robust Retries and Model Switching."""
    import time
    import random
    
    # Dynamic pose integration: ensure prompt reflects the action requested
    action_cue = prompt if "character" in prompt.lower() else f"character {prompt}"
    enhanced_prompt = (
        f"3D Pixar Disney style animation, cinematic lighting, {action_cue}, "
        "expressive face with highly detailed features, subsurface scattering, "
        "volumetric lighting, soft shadows, vibrant colors, 8k, cinematic, 9:16 aspect ratio"
    )
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # Increased retries to ensure we get a Pixar visual
    models = ["flux", "turbo", "unity"]
    max_retries = 6 # 2 attempts per model
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for attempt in range(max_retries):
        current_model = models[attempt % len(models)]
        wait_time = (attempt + 1) * 5
        
        log_agent(f"🎨 [API] Requesting Pixar 3D (Attempt {attempt+1}/{max_retries}, Model: {current_model})...")
        try:
            current_seed = random.randint(1, 9999999)
            current_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&seed={current_seed}&model={current_model}&nologo=true"
            
            response = requests.get(current_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                if len(response.content) < 10000: # Slightly higher threshold for meaningful image
                     log_agent(f"⚠️ [API] Response too small. Retrying...")
                     time.sleep(5)
                     continue
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                log_agent(f"✅ [API] Success! Pixar 3D asset generated using {current_model}.")
                return True
            elif response.status_code == 429:
                log_agent(f"⚠️ [API] Rate limited. Waiting {30 + attempt*10}s...")
                time.sleep(30 + attempt*10)
            else:
                log_agent(f"⚠️ [API] Server Error {response.status_code} on '{current_model}'. Switching...")
                time.sleep(wait_time)
        except Exception as e:
            log_agent(f"⚠️ [API] Attempt {attempt+1} failed: {str(e)}")
            time.sleep(wait_time)
            
    return False

def apply_cinematic_dof(img_path: str) -> str:
    """
    Apply a radial depth-of-field blur to the image:
    - Centre (character area) stays perfectly sharp.
    - Edges blur progressively like a real camera lens.
    Returns path to the processed image.
    """
    try:
        from PIL import Image, ImageFilter
        import numpy as np

        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        cx, cy = w // 2, h // 2

        # Vectorized radial gradient mask: white at edges (blur), dark at centre (sharp)
        ys, xs = np.mgrid[0:h, 0:w]
        dx = (xs - cx) / (w * 0.45)
        dy = (ys - cy) / (h * 0.45)
        dist = np.clip((dx**2 + dy**2) ** 0.5, 0.0, 1.0)
        mask_arr = (dist * 255).astype(np.uint8)
        mask = Image.fromarray(mask_arr)

        # Create a strongly blurred version
        blurred = img.filter(ImageFilter.GaussianBlur(radius=18))

        # Composite: sharp where mask is dark (center), blurred where mask is white (edges)
        result = Image.composite(blurred, img, mask)

        out_path = img_path.replace(".png", "_dof.png").replace(".jpg", "_dof.jpg")
        result.save(out_path)
        return out_path
    except Exception as e:
        log_agent(f"⚠️ [DOF] Depth-of-field processing failed: {e}")
        return img_path  # Fall back to original if PIL fails


def get_shorts_visual(scene_label, duration, topic_title, scene_data, img_path=None):
    """Create Excuse-Eraser-style cinematic 3D visuals.
    
    Effects applied:
    - Tight 9:16 portrait crop that fills the frame (character-forward)
    - Radial depth-of-field blur (sharp center, soft edges)
    - Diagonal Ken Burns: pan + zoom with smooth easing
    """
    if not img_path or not os.path.exists(img_path):
        visual_prompt = scene_data.get("visual_prompt", topic_title)
        os.makedirs(os.path.join(ASSETS_DIR, "ai_scenes"), exist_ok=True)
        ts = datetime.now().strftime("%H%M%S%f")
        img_path = os.path.join(ASSETS_DIR, "ai_scenes", f"pixar_{ts}.png")
        import time
        time.sleep(3.5)
        success = generate_pollinations_image(visual_prompt, img_path, timeout=60)
        if not success:
            use_premium_fallback(img_path)

    if os.path.exists(img_path):
        # Step 1: Apply cinematic depth-of-field preprocessing
        processed_path = apply_cinematic_dof(img_path)
        bg = ImageClip(processed_path).with_duration(duration)

        # Step 2: Scale to cover full 9:16 frame with extra headroom for camera movement
        # We scale to 130% of target so the diagonal pan has room to move without black bars
        w, h = bg.size
        ratio = h / float(w)
        target_ratio = 1920 / 1080.0
        scale_w = int(1080 * 1.30)
        scale_h = int(scale_w * ratio)
        if scale_h < int(1920 * 1.30):
            scale_h = int(1920 * 1.30)
            scale_w = int(scale_h / ratio)
        bg = bg.resized((scale_w, scale_h))

        # Step 3: Diagonal Ken Burns — combine pan direction + zoom with easing
        # Alternate between 4 movement patterns for visual variety across scenes
        pattern = hash(img_path) % 4
        # Pattern 0: top-left → bottom-right zoom in
        # Pattern 1: bottom-right → top-left zoom out
        # Pattern 2: top-right → bottom-left zoom in
        # Pattern 3: left-center → right-center (lateral pan, subtle)

        def make_pos(t):
            import math
            # Smooth ease-in-out curve (cubic)
            progress = t / max(duration, 0.001)
            ease = progress * progress * (3 - 2 * progress)  # smoothstep

            if pattern == 0:
                x = int(-80 + 80 * ease)   # pan right
                y = int(-60 + 60 * ease)   # pan down
            elif pattern == 1:
                x = int(80 - 80 * ease)    # pan left
                y = int(60 - 60 * ease)    # pan up
            elif pattern == 2:
                x = int(80 - 80 * ease)    # pan left
                y = int(-60 + 60 * ease)   # pan down
            else:
<<<<<<< HEAD
                x = int(-60 + 120 * ease)  # lateral pan
                y = 0

            # Center the crop, applying the offset
            final_x = (scale_w - 1080) // 2 + x
            final_y = (scale_h - 1920) // 2 + y
            return (-final_x, -final_y)

        def make_zoom(t):
            progress = t / max(duration, 0.001)
            ease = progress * progress * (3 - 2 * progress)
            if pattern in (0, 2):  # zoom in
                return 1.0 + 0.08 * ease
            else:  # zoom out
                return 1.08 - 0.08 * ease

        bg = bg.with_position(make_pos)
        bg = bg.with_effects([vfx.Resize(make_zoom)])
=======
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
>>>>>>> 93cf1b5d3343f6cf57d42df1e84761fbf7b16119
        return bg
    else:
        return ColorClip(size=TARGET_RESOLUTION, color=(20, 20, 30), duration=duration)


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
                use_premium_fallback(scene_img_path)
        else:
            log_agent(f"💎 [SCENE] Using PREMIUM pre-generated visual for {label}")
            
        # Split the scene into small chunks for memory safety
        chunk_dur = 2.5
        num_chunks = max(1, int(dur / chunk_dur))
        actual_chunk_dur = dur / num_chunks

        for chunk_idx in range(num_chunks):
            clip = get_shorts_visual(label, actual_chunk_dur, topic_title, content, img_path=scene_img_path)
            clip = clip.with_effects([vfx.FadeIn(0.15)])

            # ---------------------------------------------------------------
            # EXCUSE ERASER CHARACTER ANIMATION
            # Two sinusoidal layers composited on top of the Ken Burns base:
            #   1. Breathing (slow, 0.2 Hz, ±0.8% scale) — feels alive
            #   2. Talking pulse (fast, 3.0 Hz, ±0.6% scale) — speech rhythm
            # These are multiplied together so both effects play simultaneously.
            # ---------------------------------------------------------------
            BREATHE_HZ = 0.22   # One breath cycle every ~4.5 seconds
            TALK_HZ    = 3.0    # Fast speech pulse

            def make_char_scale(dur=actual_chunk_dur):
                import math
                def char_scale(t):
                    breathe = 1.0 + 0.008 * math.sin(2 * math.pi * BREATHE_HZ * t)
                    talk    = 1.0 + 0.006 * math.sin(2 * math.pi * TALK_HZ    * t)
                    return breathe * talk
                return char_scale

            # Vertical sway that matches the talk rhythm (character head nods slightly)
            def make_char_pos(dur=actual_chunk_dur):
                import math
                def char_pos(t):
                    nod_y = int(3 * math.sin(2 * math.pi * BREATHE_HZ * t))
                    return ("center", nod_y)
                return char_pos

            clip = clip.with_effects([vfx.Resize(make_char_scale())])
            clip = clip.with_position(make_char_pos())
            scenes.append(clip)

        current_time += dur
        gc.collect()
            
    final_video = concatenate_videoclips(scenes, method="chain")
    
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
<<<<<<< HEAD
            ).with_start(current_start).with_duration(c_dur).with_position(("center", 1150))

            # Pop-in bounce effect
            def make_pop(dur):
                def pop_animation(t):
                    if t < 0.07: return 0.65 + 5 * t
                    if t < 0.18: return 1.15 - 1.5 * (t - 0.07)
                    return 1.0
                return pop_animation

            cp = cp.with_effects([vfx.Resize(make_pop(c_dur))])
=======
            ).with_start(idx * c_dur).with_duration(c_dur).with_position(("center", 1150)) # slightly below center for visibility
            
            # Pop Effect
            def pop_animation(t):
                if t < 0.08: return 0.6 + 8 * t
                if t < 0.2: return 1.2 - 2 * (t - 0.08)
                return 1.0
            
            cp = cp.with_effects([vfx.Resize(pop_animation)])
>>>>>>> 93cf1b5d3343f6cf57d42df1e84761fbf7b16119
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
    for scene in scenes: scene.close()
    gc.collect()
    
    return out_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Viral Short")
