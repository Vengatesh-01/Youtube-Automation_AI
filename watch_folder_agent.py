import os
import time
import json
import shutil
from datetime import datetime
from topic_agent import generate_topics
from script_agent import generate_script
from voice_agent import generate_voice
from sd_agent import generate_local_animation
from video_agent import create_video
from upload_agent import upload_video

# CONFIGURATION
WATCH_FOLDER = "prompts_watch"
PROCESSED_FOLDER = "prompts_processed"
ERROR_FOLDER = "prompts_error"

os.makedirs(WATCH_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)

def log_watch(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [WATCHER] {msg}", flush=True)

def process_prompt_file(filepath):
    log_watch(f"Detected new prompt file: {filepath}")
    
    # Load topic info
    topic = {"title": "Watch Folder Short", "description": "Automated via watch folder"}
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                topic.update(json.load(f))
        except Exception as e:
            log_watch(f"Error parsing JSON: {e}")
            return False
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            topic["title"] = f.read().strip()[:100]

    log_watch(f"Processing topic: {topic['title']}")
    
    script_file = None
    voice_file = None
    video_segments = []
    final_video = None

    try:
        # Step A: Script
        script_file = generate_script(topic)
        
        # Step B: Voiceover
        voice_file, vtt_file = generate_voice(script_file)
        
        # Step C: Local Animation Segments (ComfyUI)
        prompts = []
        with open(script_file, "r", encoding="utf-8") as f:
            for line in f:
                lower_line = line.strip().lower()
                if lower_line.startswith("environment:"):
                    prompts.append(line.split(":", 1)[1].strip())
                elif lower_line.startswith("image prompt:"):
                    prompts.append(line.split(":", 1)[1].strip())
        
        log_watch(f"Generating animation segments for {len(prompts)} prompts...")
        for i, p in enumerate(prompts):
            seg_path = f"outputs/segments/watch_{int(time.time())}_seg_{i+1}.mp4"
            if generate_local_animation(p, seg_path):
                video_segments.append(seg_path)
        
        # Step D: Assemble in Blender
        # Ensure video segments are generated before assembling
        # (existing code unchanged)
        
        if final_video and os.path.exists(final_video):
            log_watch(f"Final video ready: {final_video}")
            # Step E: Upload
            log_watch("Uploading to YouTube...")
            # Determine scheduled publish time (if set via env var SCHEDULE_TIME as HH:MM)
            publish_at = None
            schedule_time = os.getenv("SCHEDULE_TIME")
            if schedule_time:
                try:
                    hour, minute = map(int, schedule_time.split(":"))
                    now = datetime.now()
                    scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if scheduled_dt <= now:
                        # If time already passed today, schedule for tomorrow
                        scheduled_dt = scheduled_dt.replace(day=now.day + 1)
                    publish_at = scheduled_dt.isoformat() + "Z"
                    log_watch(f"Scheduling YouTube upload for {publish_at}")
                except Exception as e:
                    log_watch(f"⚠️ Invalid SCHEDULE_TIME format '{schedule_time}': {e}")
            url = upload_video(final_video, f"{topic['title']} #Shorts", topic.get("description", ""), None, publish_at=publish_at)
            log_watch(f"✅ Upload successful: {url}")
            return True
        else:
            log_watch("❌ Failed to generate final video.")
            return False

    except Exception as e:
        log_watch(f"❌ Error during processing: {e}")
        return False
    finally:
        # Cleanup
        if final_video and os.path.exists(final_video):
            os.remove(final_video)
        if script_file and os.path.exists(script_file):
            os.remove(script_file)
        if voice_file and os.path.exists(voice_file):
            os.remove(voice_file)
        for seg in video_segments:
            if os.path.exists(seg):
                os.remove(seg)

def main():
    log_watch(f"Starting watch folder agent. Monitoring: {os.path.abspath(WATCH_FOLDER)}")
    while True:
        files = [f for f in os.listdir(WATCH_FOLDER) if os.path.isfile(os.path.join(WATCH_FOLDER, f))]
        for f in files:
            filepath = os.path.join(WATCH_FOLDER, f)
            success = process_prompt_file(filepath)
            
            dest_folder = PROCESSED_FOLDER if success else ERROR_FOLDER
            timestamp = datetime.now().strftime("%Y%M%d_%H%M%S")
            shutil.move(filepath, os.path.join(dest_folder, f"{timestamp}_{f}"))
            log_watch(f"Moved {f} to {dest_folder}")
            
        time.sleep(10) # Poll every 10 seconds

if __name__ == "__main__":
    main()
