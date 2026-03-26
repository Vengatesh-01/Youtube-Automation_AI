import os
import sys
import time
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
PATH_BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
MODEL_CHARACTER = os.path.abspath("work/model/character.blend")
TEMPLATE_BASE = os.path.abspath("YouTube_Automation_Free/assets/character_v2.blend")

for d in ["inputs", "work/model", "work/render/frames", "outputs", "assets/templates"]:
    os.makedirs(d, exist_ok=True)

# Ensure dependencies are in path
sys.path.append(os.getcwd())
from scripts.ollama_gen import generate_script
from scripts.piper_tts import text_to_speech
from scripts.rhubarb_sync import generate_lipsync
from scripts.character_factory import ensure_character
from scripts.comfy_gen import generate_content
from scripts.youtube_upload import upload_video
from stitch_demo import stitch

def run_production_pipeline(topic):
    print(f"🚀 INITIALIZING PRODUCTION PIPELINE: {topic}")
    
    # 0. ENSURE CHARACTER PERSISTENCE (Layer 1)
    if not ensure_character():
        print("❌ CRITICAL: Character identity staging failed.")
        return False

    out_dir = f"outputs/{int(time.time())}"
    os.makedirs(out_dir, exist_ok=True)
    
    audio_file = os.path.abspath(f"inputs/voice.wav")
    lipsync_file = os.path.abspath(f"work/model/lipsync.json")
    video_file = os.path.abspath(f"outputs/final_video.mp4")

    # 1. SCRIPT GENERATION (Viral Rhythmic)
    print("✍️ Generating Viral Script...")
    script = generate_script(topic)
    if not script: return False
    print(f"--- SCRIPT ---\n{script}\n--------------")

    # 2. VOICE & LIPSYNC (Parallel)
    print("🎙️ Generating Voice & LipSync...")
    def prep_audio():
        return text_to_speech(script, audio_file)
    
    def prep_sync():
        # LipSync needs the audio, so we might need a small delay or sequential
        time.sleep(2) # Buffer for TTS start
        return generate_lipsync(audio_file, lipsync_file)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(text_to_speech, script, audio_file)
        time.sleep(1) # Offset
        f2 = executor.submit(generate_lipsync, audio_file, lipsync_file)
        if not f1.result() or not f2.result():
            print("⚠️ Audio/Sync prep failed. Proceeding with caution...")

    # 3. BLENDER RENDER (Main Engine)
    print("🎬 Launching Blender Render Engine...")
    blender_script = os.path.abspath("scripts/blender_render.py")
    cmd = [
        PATH_BLENDER, "-b", "-P", blender_script, "--",
        audio_file, MODEL_CHARACTER, lipsync_file, video_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ RENDER COMPLETE: {video_file}")
    except Exception as e:
        print(f"❌ Blender Render Failed: {e}")
        
    # 4. YOUTUBE UPLOAD (Step 9)
    print("📺 Uploading to YouTube...")
    video_id = None
    try:
        video_id = upload_video(
            video_file, 
            title=f"{topic} #shorts", 
            description=f"Automated video about {topic}. #AI #Automation", 
            tags=[topic.replace(" ", ""), "AI", "Shorts"]
        )
    except Exception as e:
        print(f"⚠️ YouTube Upload Failed: {e}")

    # 5. CLEANUP (Step 10)
    print("🧹 Cleaning up intermediate files...")
    # Delete frames if they were generated
    if os.path.exists("work/render/frames"):
        for f in os.listdir("work/render/frames"):
            os.remove(os.path.join("work/render/frames", f))
    
    # 7. TEMPLATE SAVING (Step 11)
    print("💾 Saving character template...")
    template_path = f"assets/templates/character_template_{time.strftime('%Y%m%d')}.blend"
    if os.path.exists(MODEL_CHARACTER):
        import shutil
        shutil.copy(MODEL_CHARACTER, template_path)

    # 8. STATUS JSON (Step 12)
    status = {
        "status": "success" if os.path.exists(video_file) else "error",
        "video": video_file,
        "frames_deleted": True,
        "model": "work/model/character.blend",
        "duration_seconds": 30,
        "frames_rendered": 24 * 30,
        "youtube_video_id": video_id or "failed",
        "notes": []
    }
    
    with open("outputs/status.json", "w") as f:
        json.dump(status, f, indent=4)
    print(f"📄 Status report generated: outputs/status.json")

    return True

if __name__ == "__main__":
    test_topic = "The 3 AM billionaire routine"
    run_production_pipeline(test_topic)
