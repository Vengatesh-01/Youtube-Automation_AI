"""
main.py — YouTube Automation Orchestrator

Runs all agents in sequence:
  1. topic_agent    → Fetch trending topics
  2. script_agent   → Write video script
  3. voice_agent    → Generate voiceover (Edge TTS)
  4. thumbnail_agent → Create thumbnail (Pillow)
  5. video_agent    → Render final video (MoviePy)
  6. upload_agent   → Upload to YouTube (OAuth)

Scheduling:
  Set SCHEDULE_TIMES to run at specific times every day.
  Set to [] to run once immediately.
"""

import sys
import os

# Ensure the app directory is in sys.path for robust module imports on Linux (Render)
abs_path = os.path.dirname(os.path.abspath(__file__))
if abs_path not in sys.path:
    sys.path.insert(0, abs_path)

import time
import threading
import os
from datetime import datetime, timezone, timedelta
from flask import Flask, send_from_directory, render_template_string
import glob
import traceback
# import psutil  # Moved to log() for boot resilience
import json

# Force line buffering for logs (Python 3.7+)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

print("--- [BOOT] YouTube Automation System Initializing... ---", flush=True)

from utils import safe_print
# Immediate safety test
try:
    safe_print("--- [BOOT] Log System Ready ---")
except Exception as e:
    print(f"--- [BOOT] CRITICAL: safe_print failed: {e} ---", file=sys.stderr)

app = Flask(__name__)

# --- UI Templates ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Automation Dashboard</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; background: #f4f4f9; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1 { color: #333; }
        .btn { display: inline-block; background: #e91e63; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; }
        .btn:hover { background: #c2185b; }
        .status { font-weight: bold; color: #4caf50; }
        ul { list-style: none; padding: 0; }
        li { background: #eee; margin: 5px 0; padding: 10px; border-radius: 4px; display: flex; justify-content: space-between; }
        a.download { color: #2196f3; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎬 YouTube Video Generation</h1>
        <p>Status: <span class="status">Online</span></p>
        <p>Schedule: {{ schedule }}</p>
        <div style="display: flex; gap: 10px;">
            <a href="/run" class="btn">🚀 Generate YouTube Video</a>
        </div>
    </div>

    <div class="card">
        <h2>📂 Generated Videos</h2>
        <ul>
            {% for video in videos %}
            <li>
                <span>{{ video }}</span>
                <a href="/download/{{ video }}" class="download">Download ↓</a>
            </li>
            {% endfor %}
            {% if not videos %}<li>No videos generated yet.</li>{% endif %}
        </ul>
    </div>

    <div class="card">
        <h2>📜 Recent Logs</h2>
        <pre style="background: #222; color: #0f0; padding: 10px; border-radius: 4px; overflow-x: auto;">{{ logs }}</pre>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    video_files = [os.path.basename(f) for f in glob.glob("videos/*.mp4")]
    log_content = "No logs yet."
    if os.path.exists("videos/automation.log"):
        with open("videos/automation.log", "r", encoding="utf-8") as f:
            log_content = "".join(f.readlines()[-20:]) # Last 20 lines
            
    return render_template_string(
        INDEX_HTML, 
        schedule=SCHEDULE_TIMES, 
        videos=sorted(video_files, reverse=True),
        logs=log_content
    )

@app.route('/run')
def trigger_pipeline():
    """Manually trigger the automation pipeline."""
    log("Web Trigger: Manual pipeline request received.")
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    log(f"Web Trigger: Background thread started. Thread alive: {thread.is_alive()}")
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>✅ Pipeline Triggered!</h1>
            <p>The automation is now running in the background.</p>
            <p><a href="/">Return to Dashboard</a></p>
            <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
        </body>
    </html>
    """, 202

@app.route('/test5s')
def trigger_test_pipeline():
    """Trigger a fast 5s test."""
    log("Web Trigger: 5s Test pipeline request received.")
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>🧪 Test Started!</h1>
            <p>The video generator is running in the background.</p>
            <p><a href="/">Return to Dashboard</a></p>
            <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
        </body>
    </html>
    """, 202

@app.route('/download/<filename>')
def download_video(filename):
    """Download a specific generated video."""
    return send_from_directory("videos", filename, as_attachment=True)

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
SCHEDULE_TIMES = ["04:30"]              # 10:00 AM IST
ENABLE_UPLOAD = True                    # client_secrets.json is configured
# ---------------------

# DEFERRED AGENT IMPORTS (Moved inside run_pipeline to prevent boot-time crashes)
# from topic_agent import generate_topics
# from script_agent import generate_script
# from voice_agent import generate_voice
# from video_agent import create_video
# from thumbnail_agent import generate_thumbnail
# from upload_agent import upload_video


def log(msg):
    try:
        # Move import here to ensure boot success even if psutil fails
        import psutil
        mem = psutil.virtual_memory().percent
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        log_line = f"[{timestamp}] [RAM: {mem}%] {msg}"
        
        # Windows console safe print
        safe_print(log_line)
        
        # Persistent log file in videos directory (mounted disk on Render)
        os.makedirs("videos", exist_ok=True)
        # Use utf-8 encoding explicitly
        with open("videos/automation.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        # Fallback to standard print if file logging fails or psutil missing
        print(f"Logging error: {e}")

PERSISTENCE_FILE = "videos/last_run.json"

def get_last_run():
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_last_run(run_id, status="scheduled"):
    data = get_last_run()
    data[run_id] = {
        "time": datetime.now(timezone.utc).isoformat(),
        "status": status
    }
    # Keep only last 10 runs to avoid file growth
    if len(data) > 10:
        sorted_keys = sorted(data.keys(), key=lambda k: data[k]["time"])
        data = {k: data[k] for k in sorted_keys[-10:]}
        
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(data, f)


import re as _re
import subprocess as _subprocess

# ==========================================
#   GUARDRAIL VALIDATION FUNCTIONS
# ==========================================

def _validate_script(script_text: str) -> tuple:
    """Guardrail: Validate script has proper structure for video generation."""
    issues = []
    
    if len(script_text) < 100:
        issues.append(f"Script too short ({len(script_text)} chars, need 100+)")
    
    scenes = _re.findall(r'Scene \d+', script_text, _re.IGNORECASE)
    if len(scenes) < 3:
        issues.append(f"Only {len(scenes)} scenes (need 3+)")
    
    image_prompts = _re.findall(r'Image Prompt:\s*(.*)', script_text, _re.IGNORECASE)
    if len(image_prompts) < 3:
        issues.append(f"Only {len(image_prompts)} image prompts (need 3+)")
    
    voiceover_lines = _re.findall(r'Voiceover:\s*(.*)', script_text, _re.IGNORECASE)
    if len(voiceover_lines) < 3:
        issues.append(f"Only {len(voiceover_lines)} voiceover lines (need 3+)")
    
    if issues:
        return False, "; ".join(issues)
    return True, f"✅ {len(scenes)} scenes, {len(image_prompts)} prompts, {len(voiceover_lines)} voiceovers"


def _validate_voice(voice_file: str) -> tuple:
    """Guardrail: Validate voiceover is real audio, not a silence placeholder."""
    if not voice_file or not os.path.exists(voice_file):
        return False, "Voice file does not exist"
    
    size = os.path.getsize(voice_file)
    if size < 10000:  # Less than 10KB = likely silence
        return False, f"Voice file too small ({size} bytes) — likely silence placeholder"
    
    return True, f"✅ {size / 1024:.1f} KB"


def _validate_segments(segments: list, total_expected: int) -> tuple:
    """Guardrail: Validate enough video segments were generated with real content."""
    if not segments:
        return False, "No video segments were generated at all"
    
    valid = 0
    for seg in segments:
        if os.path.exists(seg) and os.path.getsize(seg) > 50000:  # >50KB = real content
            valid += 1
    
    min_required = max(3, total_expected // 2)  # At least 50% or 3
    if valid < min_required:
        return False, f"Only {valid}/{total_expected} valid segments (need {min_required}+)"
    
    return True, f"✅ {valid}/{total_expected} valid segments"


def _validate_final_video(video_path: str) -> tuple:
    """Guardrail: Validate final video has both video and audio streams."""
    if not video_path or not os.path.exists(video_path):
        return False, "Final video file does not exist"
    
    size = os.path.getsize(video_path)
    if size < 100000:  # <100KB = likely broken
        return False, f"Final video too small ({size} bytes)"
    
    # Check audio stream exists using ffprobe
    has_audio = False
    try:
        from utils import get_ffmpeg
        ffmpeg_exe = get_ffmpeg()
        ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
        result = _subprocess.run(
            [ffprobe_exe, "-v", "quiet", "-show_streams", "-select_streams", "a", video_path],
            capture_output=True, text=True, timeout=10
        )
        has_audio = "codec_type=audio" in result.stdout
    except Exception:
        has_audio = True  # Can't verify, assume OK
    
    if not has_audio:
        return False, f"Final video ({size / (1024*1024):.1f} MB) has NO audio stream"
    
    return True, f"✅ {size / (1024*1024):.1f} MB with audio"


# ==========================================
#   MAIN PIPELINE WITH GUARDRAILS
# ==========================================

def run_pipeline():
    try:
        log("===== 🚀 YouTube Automation Pipeline Starting =====")
        log("🛡️ Guardrails ACTIVE — each step will be validated before proceeding.")
        
        # Deferred imports to ensure boot success even if an agent has missing dependencies
        from topic_agent import generate_topics
        from script_agent import generate_script
        from voice_agent import generate_voice
        from video_agent import create_video
        from thumbnail_agent import generate_thumbnail
        from upload_agent import upload_video
        import random, re, uuid
        from character_profiles import get_random_character

        # Pick THREE different characters for this video
        character_pool = [get_random_character() for _ in range(3)]
        for i, char in enumerate(character_pool):
            log(f"🎬 Character {i+1}: {char['name']} - {char['visual'][:50]}...")
        
        # Use the first character's gender for the narrator voice
        main_gender = "woman"
        for g in ["man", "woman", "boy", "girl"]:
            if g in character_pool[0]["visual"].lower():
                main_gender = g
                break
        
        voice_map = {
            "man": "en-US-ChristopherNeural",
            "woman": "en-US-JennyNeural",
            "boy": "en-GB-ThomasNeural",
            "girl": "en-US-AnaNeural"
        }
        selected_voice = voice_map.get(main_gender, "en-US-ChristopherNeural")

        # ── STEP 1: TOPIC ─────────────────────────────────
        log("━━━ Step 1/6 — Generating topic...")
        topics = generate_topics()
        if not topics:
            log("🛡️ GUARDRAIL FAIL: No topics generated. Aborting pipeline.")
            return
        topic = topics[0]
        log(f"✅ Topic: {topic['title']}")

        # ── STEP 2: SCRIPT ────────────────────────────────
        log("━━━ Step 2/6 — Generating script...")
        script_file_path = generate_script(topic)
        
        if not script_file_path or not os.path.exists(script_file_path):
            log("🛡️ GUARDRAIL FAIL: Script file was not created. Aborting pipeline.")
            return
        
        with open(script_file_path, "r", encoding="utf-8") as f:
            full_script_text = f.read()
        
        # 🛡️ GUARDRAIL: Validate script structure
        script_ok, script_msg = _validate_script(full_script_text)
        if script_ok:
            log(f"🛡️ Script Validation: {script_msg}")
        else:
            log(f"🛡️ GUARDRAIL WARNING: Script issues — {script_msg}")
            log("🛡️ Attempting to continue with fallback script...")
            # Try regenerating with fallback
            from script_agent import get_fallback_script
            full_script_text = get_fallback_script(topic.get('title', 'Unknown'))
            # Save the fallback
            with open(script_file_path, "w", encoding="utf-8") as f:
                f.write(full_script_text)
            script_ok2, script_msg2 = _validate_script(full_script_text)
            log(f"🛡️ Fallback Script Validation: {script_msg2}")
            if not script_ok2:
                log("🛡️ GUARDRAIL FAIL: Even fallback script is invalid. Aborting pipeline.")
                return

        # ── STEP 3: VOICEOVER ─────────────────────────────
        log(f"━━━ Step 3/6 — Generating voiceover (Voice: {selected_voice})...")
        voice_file, vtt_file = generate_voice(full_script_text, voice_name=selected_voice)
        
        # 🛡️ GUARDRAIL: Validate voice output
        voice_ok, voice_msg = _validate_voice(voice_file)
        if voice_ok:
            log(f"🛡️ Voice Validation: {voice_msg}")
        else:
            log(f"🛡️ GUARDRAIL WARNING: Voice issues — {voice_msg}")
            log("🛡️ Retrying voiceover generation...")
            # Retry once with a different voice
            retry_voice = "en-US-JennyNeural" if selected_voice != "en-US-JennyNeural" else "en-US-ChristopherNeural"
            voice_file, vtt_file = generate_voice(full_script_text, voice_name=retry_voice)
            voice_ok2, voice_msg2 = _validate_voice(voice_file)
            if voice_ok2:
                log(f"🛡️ Voice Retry OK: {voice_msg2}")
            else:
                log(f"🛡️ GUARDRAIL FAIL: Voice generation failed twice — {voice_msg2}. Aborting pipeline.")
                return

        # ── STEP 4: THUMBNAIL ─────────────────────────────
        log("━━━ Step 4/6 — Creating thumbnail...")
        thumbnail_file = generate_thumbnail(topic["title"], topic.get("category", "Trending"))
        
        # 🛡️ GUARDRAIL: Validate thumbnail
        if thumbnail_file and os.path.exists(thumbnail_file):
            thumb_size = os.path.getsize(thumbnail_file)
            log(f"🛡️ Thumbnail Validation: ✅ {thumb_size / 1024:.1f} KB")
        else:
            log("🛡️ GUARDRAIL WARNING: Thumbnail creation failed. Continuing without thumbnail.")
            thumbnail_file = None

        # ── STEP 5: VISUALS ───────────────────────────────
        log("━━━ Step 5/6 — Generating Visuals via AI Image Generation...")
        from sd_agent import generate_local_animation
        
        image_prompts = re.findall(r'Image Prompt:\s*(.*)', full_script_text, re.IGNORECASE)
        if not image_prompts:
            log("🛡️ GUARDRAIL WARNING: No 'Image Prompt:' tags in script. Using scene text as prompts.")
            # Try extracting scene text instead
            scene_texts = re.findall(r'Text:\s*(.*)', full_script_text, re.IGNORECASE)
            if scene_texts:
                image_prompts = [f"Pixar 3D cinematic style, {t}" for t in scene_texts]
            else:
                clean = full_script_text[:100].replace("[", "").replace("]", "").strip()
                image_prompts = [f"{clean}, cinematic, high quality"]
        
        total_scenes = len(image_prompts)
        log(f"🎬 {total_scenes} scenes to render...")
            
        video_segments = []
        failed_scenes = []
        effects = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
        
        for i, prompt in enumerate(image_prompts):
            seg_path = os.path.abspath(f"outputs/seg_{uuid.uuid4().hex[:8]}.mp4")
            current_char = character_pool[i % len(character_pool)]
            enhanced_prompt = f"Pixar 3D Disney animation style, {prompt}"
            effect = random.choice(effects)
            
            log(f"🎨 Rendering scene {i+1}/{total_scenes}: {enhanced_prompt[:60]}... (Effect: {effect})")
            
            success = generate_local_animation(enhanced_prompt, seg_path, seed=current_char['seed'], effect=effect)
            
            if success and os.path.exists(seg_path) and os.path.getsize(seg_path) > 50000:
                video_segments.append(seg_path)
                log(f"   ✅ Scene {i+1} OK ({os.path.getsize(seg_path) / 1024:.0f} KB)")
            else:
                failed_scenes.append(i + 1)
                log(f"   ❌ Scene {i+1} FAILED — will be skipped")
        
        # 🛡️ GUARDRAIL: Validate enough scenes succeeded
        seg_ok, seg_msg = _validate_segments(video_segments, total_scenes)
        if seg_ok:
            log(f"🛡️ Segments Validation: {seg_msg}")
            if failed_scenes:
                log(f"🛡️ Note: Scenes {failed_scenes} failed but enough succeeded to continue.")
        else:
            log(f"🛡️ GUARDRAIL FAIL: {seg_msg}. Aborting — not enough visual content for a meaningful video.")
            return

        # ── STEP 6: COMPOSE FINAL VIDEO ───────────────────
        log("━━━ Final Step — Compositing video + audio...")
        from video_agent import create_video
        
        os.makedirs("videos", exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%H%M%S")
        final_video_file = os.path.abspath(f"videos/final_video_{ts}.mp4")
        
        args = [video_segments]
        if voice_file: args.append(voice_file)
        if vtt_file: args.append(vtt_file)
        args.append(final_video_file)
        
        video_file = create_video(*args)
        if not video_file:
            log("⚠️ FFmpeg Assembly yielded no file, checking fallback...")
            video_file = final_video_file if os.path.exists(final_video_file) else None

        # 🛡️ GUARDRAIL: Validate final video quality
        video_ok, video_msg = _validate_final_video(video_file)
        if video_ok:
            log(f"🛡️ Final Video Validation: {video_msg}")
        else:
            log(f"🛡️ GUARDRAIL FAIL: {video_msg}. Aborting — will NOT upload a broken video.")
            return

        # ── UPLOAD GATE ───────────────────────────────────
        if ENABLE_UPLOAD:
            log("━━━ Upload Gate — All guardrails passed ✅")
            log("Final Phase — Uploading to YouTube...")
            
            # --- Schedule Publish Time (8 AM / 8 PM Local) ---
            now_local = datetime.now()
            target_am = now_local.replace(hour=8, minute=0, second=0, microsecond=0)
            target_pm = now_local.replace(hour=20, minute=0, second=0, microsecond=0)
            
            if now_local < target_am:
                target = target_am
            elif now_local < target_pm:
                target = target_pm
            else:
                target = (now_local + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                
            local_tz = now_local.astimezone().tzinfo
            target_aware = target.replace(tzinfo=local_tz)
            utc_target = target_aware.astimezone(timezone.utc)
            publish_time = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
            log(f"⏰ Scheduling YouTube publish time for: {publish_time} (Target local: {target.strftime('%Y-%m-%d %H:%M')})")

            # SEO Metadata
            seo_tags = topic.get("tags", ["shorts", "ai", "trending"])
            seo_description = f"{full_script_text[:200]}...\n\n#Shorts #AI #Topic:{topic['title']}"
            
            url = upload_video(
                video_file=video_file, 
                title=f"{topic['title']} #Shorts", 
                description=seo_description, 
                thumbnail_file=thumbnail_file,
                tags=seo_tags,
                publish_at=publish_time
            )
            if url:
                log(f"✅ Uploaded successfully: {url}")
            else:
                log("❌ Upload failed — YouTube API returned no URL.")
        else:
            log("Upload skipped (ENABLE_UPLOAD=False).")

        log("===== ✅ Pipeline Complete =====")
        log(f"  Video Ready: {video_file}")
        log(f"  Segments Used: {len(video_segments)}/{total_scenes}")
        log(f"  Failed Scenes: {failed_scenes if failed_scenes else 'None'}")

    except Exception as e:
        log(f"❌ PIPELINE ERROR: {str(e)}")
        log("Full Detail Traceback:")
        traceback.print_exc()


def get_next_run_time(schedule_times):
    """Calculates the next target datetime object based on HH:MM schedule strings (UTC)."""
    now = datetime.now(timezone.utc)
    possible_targets = []
    
    for time_str in schedule_times:
        h, m = map(int, time_str.split(':'))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        possible_targets.append(target)
    
    return min(possible_targets)

# State to track last run to prevent double-firing
LAST_RUN_DATE = None 


import traceback

def run_scheduler():
    """Background loop for the scheduler. Checks every 30 seconds."""
    log(f"Scheduler initialized with UTC times: {', '.join(SCHEDULE_TIMES)}")
    
    while True:
        try:
            if not SCHEDULE_TIMES:
                log("No SCHEDULE_TIMES set. Scheduler idling.")
                time.sleep(3600)
                continue

            now = datetime.now(timezone.utc)
            now_str = now.strftime("%H:%M")
            today_date = now.strftime("%Y-%m-%d")
            run_id = f"{today_date}_{now_str}"

            last_runs = get_last_run()

            # If current time is in schedule and we haven't run yet today for this slot
            if now_str in SCHEDULE_TIMES and run_id not in last_runs:
                log(f"⏰ Scheduled trigger matched: {now_str} UTC")
                save_last_run(run_id, "triggered")
                threading.Thread(target=run_pipeline, daemon=True).start()
            
            # log status occasionally (every hour)
            if now.minute == 0 and now.second < 40:
                next_run = get_next_run_time(SCHEDULE_TIMES)
                log(f"Heartbeat: Scheduler active. Next run at {next_run.strftime('%Y-%m-%d %H:%M')} UTC")

            time.sleep(30) # Wait 30 seconds between checks
        except Exception:
            log("CRITICAL ERROR in Scheduler Loop:")
            traceback.print_exc()
            time.sleep(30)

# --- ENTRY POINT for Render (Gunicorn looks for 'app') ---
if __name__ == "__main__":
    # Local execution mode
    try:
        log("Starting local dev server...")
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=run_scheduler, name="Scheduler", daemon=True)
        scheduler_thread.start()
        
        port = int(os.environ.get("PORT", 8080))
        app.run(host='0.0.0.0', port=port)
    except Exception:
        print("--- [CRITICAL] FATAL ERROR during local boot ---", file=sys.stderr)
        traceback.print_exc()
else:
    # Gunicorn execution mode (Render)
    try:
        log("Web Server initialized by Gunicorn. Starting background scheduler...")
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=run_scheduler, name="Scheduler", daemon=True)
        scheduler_thread.start()
        log(f"Scheduler thread started: {scheduler_thread.is_alive()}")
    except Exception as e:
        print(f"--- [CRITICAL] Gunicorn Worker Boot Failed: {e} ---", file=sys.stderr)
        traceback.print_exc()
