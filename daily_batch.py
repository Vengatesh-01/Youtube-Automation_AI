import os
import json
import time
from datetime import datetime
from topic_agent import generate_topics
from script_agent import generate_script
from voice_agent import generate_voice
from comfy_agent import generate_local_animation
from video_agent import create_video
from upload_agent import upload_video
from utils import safe_print

STATUS_FILE = "daily_status.json"

def log_batch(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [BATCH] {msg}"
    safe_print(line)
    with open("batch_automation.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_prompts_from_script(script_file):
    """
    Extracts key frame descriptions from the script file.
    Expects 'Environment' lines for background prompts.
    """
    prompts = []
    if not os.path.exists(script_file): return []
    with open(script_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("Environment:"):
                p = line.split("Environment:")[1].strip()
                prompts.append(p)
    return prompts

def run_daily_batch():
    log_batch("Starting daily batch of 3 shorts (Local Only)...")
    
    # 1. Fetch 3 topics
    topics = generate_topics(3)
    history = []

    for i, topic in enumerate(topics):
        short_id = i + 1
        log_batch(f"--- Processing Short {short_id}/3: {topic['title']} ---")
        
        script_file = None
        voice_file = None
        video_segments = []
        final_video = None

        try:
            # Step A: Script
            script_file = generate_script(topic)
            
            # Step B: Voiceover
            voice_file = generate_voice(script_file)
            
            # Step C: Local Animation Segments (ComfyUI)
            key_prompts = parse_prompts_from_script(script_file)
            log_batch(f"Generating {len(key_prompts)} local animation segments...")
            for j, p in enumerate(key_prompts):
                seg_path = f"outputs/segments/short_{short_id}_seg_{j+1}.mp4"
                if generate_local_animation(p, seg_path):
                    video_segments.append(seg_path)
            
            # Step D: Assemble in Blender
            final_video = create_video(script_file, voice_file, topic["title"], video_segments)
            
            if not final_video or not os.path.exists(final_video):
                raise Exception(f"Final video assembly failed.")

            # Step E: Upload
            log_batch(f"Uploading {topic['title']} to YouTube...")
            url = upload_video(final_video, f"{topic['title']} #Shorts", topic.get("description", ""), None)
            
            # Step F: Status
            if url:
                log_batch(f"✅ Upload successful: {url}")
            
            history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "short_id": short_id,
                "title": topic["title"],
                "url": url,
                "status": "Success" if url else "Rendered but not uploaded"
            })

        except Exception as e:
            log_batch(f"❌ Error in Short {short_id}: {e}")
            history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "short_id": short_id,
                "title": topic["title"],
                "status": f"Failed: {str(e)}"
            })
        finally:
            # Comprehensive Cleanup (Requirement 8)
            log_batch(f"Cleaning up temporary files for Short {short_id}...")
            if final_video and os.path.exists(final_video):
                os.remove(final_video)
            if script_file and os.path.exists(script_file):
                os.remove(script_file)
            if voice_file and os.path.exists(voice_file):
                os.remove(voice_file)
            for seg in video_segments:
                if os.path.exists(seg):
                    os.remove(seg)
            log_batch("Cleanup complete.")

    # Save Batch Status (JSON log)
    log_data = []
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                log_data = json.load(f)
        except:
            log_data = []
    
    log_data.extend(history)
    
    with open(STATUS_FILE, "w") as f:
        json.dump(log_data, f, indent=4)

    log_batch("Daily batch process complete.")

if __name__ == "__main__":
    run_daily_batch()
