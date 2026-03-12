import os
import json
import uuid
from datetime import datetime
from script_agent import generate_script
from voice_agent import generate_voice
from video_agent import create_video
from utils import safe_print

def run_production(topic_title="The Unseen Strength"):
    safe_print(f"🎬 [START] Starting Full Cinematic Production for: {topic_title}")
    
    # 1. Topic Dict
    topic = {"title": topic_title}
    
    # 2. Generate Cinematic Script
    safe_print("✍️ [1/4] Generating AI Director's Script...")
    script_path = generate_script(topic)
    if not script_path:
        safe_print("❌ Failed to generate script.")
        return
    
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
    
    # 3. Generate Voice
    safe_print("🔊 [2/4] Generating Professional Voiceover...")
    voice_file = generate_voice(script_text)
    if not voice_file:
        safe_print("❌ Failed to generate voiceover.")
        return
        
    # 4. Create Video (Blender Cinematic + FFmpeg Fusion)
    safe_print("🎥 [3/4] Rendering 3D Animation & Fusing Audio...")
    video_id = datetime.now().strftime("%H%M%S")
    output_video = f"videos/cinematic_short_{video_id}.mp4"
    
    try:
        final_path = create_video(script_text, voice_file, output_video)
        safe_print(f"🎉 [SUCCESS] Production complete! Final Video: {final_path}")
    except Exception as e:
        safe_print(f"❌ [ERROR] Production failed at video stage: {e}")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "The Courage to Fail"
    run_production(topic)
