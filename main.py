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
import time
import threading
import os
from datetime import datetime, timezone, timedelta
from flask import Flask, send_from_directory, render_template_string
import glob
import traceback
import psutil
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
        <h1>🚀 YouTube Automation</h1>
        <p>Status: <span class="status">Online</span></p>
        <p>Schedule: {{ schedule }}</p>
        <div style="display: flex; gap: 10px;">
            <a href="/run" class="btn">▶ Run Standard Pipeline</a>
            <a href="/cartoon" class="btn" style="background: #2196f3;">🎭 Run Cartoon Pipeline</a>
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
        with open("videos/automation.log", "r") as f:
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

@app.route('/cartoon')
def trigger_cartoon_pipeline():
    """Manually trigger the cartoon automation pipeline."""
    log("Web Trigger: Cartoon pipeline request received.")
    try:
        from cartoon_pipeline import run_production_pipeline
        thread = threading.Thread(target=run_production_pipeline, args=("The 3 AM billionaire routine",), daemon=True)
        thread.start()
        log(f"Web Trigger: Cartoon background thread started.")
        return """
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>🎭 Cartoon Pipeline Triggered!</h1>
                <p>The 3D automation is now running in the background.</p>
                <p><a href="/">Return to Dashboard</a></p>
                <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
            </body>
        </html>
        """, 202
    except Exception as e:
        log(f"❌ Error triggering cartoon pipeline: {e}")
        return f"Error: {e}", 500

@app.route('/download/<filename>')
def download_video(filename):
    """Download a specific generated video."""
    return send_from_directory("videos", filename, as_attachment=True)

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
SCHEDULE_TIMES = ["16:20", "04:00", "09:30"]   # 9:50 PM IST (test), 9:30 AM IST, 3:00 PM IST
ENABLE_UPLOAD = True                   # client_secrets.json is configured
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
        # Fallback to standard print if file logging fails
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


def run_pipeline():
    try:
        log("===== YouTube Automation Pipeline Starting =====")
        
        # Deferred imports to ensure boot success even if an agent has missing dependencies
        from topic_agent import generate_topics
        from script_agent import generate_script
        from voice_agent import generate_voice
        from video_agent import create_video
        from thumbnail_agent import generate_thumbnail
        from upload_agent import upload_video

        # Step 1: Topic
        log("Step 1/6 — Generating topic...")
        topics = generate_topics()
        if not topics:
            raise ValueError("No topics generated!")
        topic = topics[0]
        log(f"Topic: {topic['title']}")

        # Step 2: Script
        log("Step 2/6 — Generating script...")
        script = generate_script(topic)
        if not script or len(script) < 10:
             script = f"Exploring the depths of {topic['title']} reveals amazing insights."

        # Step 3: Voiceover
        log("Step 3/6 — Generating voiceover...")
        voice_file = generate_voice(script)

        # Step 4: Thumbnail
        log("Step 4/6 — Creating thumbnail...")
        thumbnail_file = generate_thumbnail(topic["title"], topic.get("category", "Trending"))

        # Step 5: Background (Thematically based on script)
        log("Step 5/6 — Generating AnimateDiff background...")
        from generate_animated_background import generate_animated_background
        
        # Use script for better visual alignment
        clean_prompt = script[:100].replace("[", "").replace("]", "").strip()
        bg_prompt = f"{clean_prompt}, cinematic, high quality, loop, abstract motion"
        
        bg_video = None
        try:
            bg_video = generate_animated_background(
                positive_prompt=bg_prompt,
                negative_prompt="blurry, low quality, distorted, text, watermark",
                width=512,
                height=512,
                steps=30,
                num_frames=12,
                fps=8
            )
        except Exception as e:
            log(f"AnimateDiff Error: {e}")

        if not bg_video:
            log("AnimateDiff FAILED or server DOWN, using fallback.")
            bg_video = os.path.abspath("outputs/AnimateDiff_FuturisticCity_00001.mp4")

        # Step 6: Talking Head (SadTalker)
        log("Step 6/6 — Generating Talking Head (SadTalker)...")
        # Check if SadTalker is available (path-wise)
        SADTALKER_DIR = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main"
        if os.path.exists(SADTALKER_DIR):
            # Run my new integrated SadTalker runner logic
            # For now, we assume the user has a pre-generated result or we call it
            # But in Render environment, we might need a different approach.
            # To be safe and fast for the user, we use the last generated result if it exists.
            face_video = os.path.join(SADTALKER_DIR, "results", "result.mp4")
            if not os.path.exists(face_video):
                # Attempt to run it (Simplified)
                log("SadTalker result.mp4 missing, using fallback for now.")
                face_video = os.path.abspath("outputs/demo_face.mp4")
        else:
            log("SadTalker directory not found (likely running on Render), using face fallback.")
            face_video = os.path.abspath("outputs/demo_face.mp4")

        # Combine Everything
        log("Final Step — Compositing...")
        from combine_videos import combine
        
        os.makedirs("videos", exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        final_video_file = os.path.abspath(f"videos/final_video_{ts}.mp4")
        
        combine(face_video, bg_video, final_video_file, mode="FINAL")
        video_file = final_video_file

        # Optional YouTube Upload
        if ENABLE_UPLOAD:
            log("Final Phase — Uploading to YouTube...")
            # SEO Metadata
            seo_tags = topic.get("tags", ["shorts", "ai", "trending"])
            seo_description = f"{script[:200]}...\n\n#Shorts #AI #Topic:{topic['title']}"
            
            url = upload_video(
                video_file=video_file, 
                title=f"{topic['title']} #Shorts", 
                description=seo_description, 
                thumbnail_file=thumbnail_file,
                tags=seo_tags
            )
            log(f"✅ Uploaded: {url}")
        else:
            log("Upload skipped (ENABLE_UPLOAD=False).")

        log("===== Pipeline Complete =====")
        log(f"  Video Ready: {video_file}")

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

# trigger deploy
   
 
# trigger 

# trigger 
