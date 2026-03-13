import os
import time
import random
from datetime import datetime
from utils import safe_print

# Ensure we're offline
os.environ["AUTO_SYNC_TO_CLOUD"] = "false"

def run_offline_automation():
    safe_print("🤖 [OFFLINE AUTOMATION] Starting Local YouTube Factory...")
    
    # 1. Choose 1-3 videos to make today
    num_videos = random.randint(1, 3)
    safe_print(f"🎬 [SCHEDULE] Generating {num_videos} video(s) today.")

    topics = [
        "The Law of Attraction",
        "Overcoming Procrastination",
        "The Power of Habits",
        "Growth Mindset secrets",
        "Financial Freedom principles",
        "The Art of Focus",
        "Building Unstoppable Confidence",
        "Dealing with Failure",
        "Morning Routines of the Wealthy",
        "How to Stop Overthinking"
    ]
    
    for i in range(num_videos):
        selected_topic = random.choice(topics)
        safe_print(f"\n--- 🎥 Video {i+1}/{num_videos} ---")
        safe_print(f"💡 [TOPIC] Selected Topic: {selected_topic}")
        
        # 2. Generate Script (Local Llama3 or Fallback)
        safe_print("✍️ [SCRIPT] Generating local script...")
        from script_agent import generate_script
        topic_dict = {"title": selected_topic}
        
        try:
            # Check if ollama is running locally, otherwise use emergency fallback immediately
            import requests
            try:
                requests.get("http://localhost:11434/api/tags", timeout=2)
                script_file = generate_script(topic_dict)
            except:
                safe_print(f"⚠️ [WARNING] Local Ollama is offline. Using built-in offline fallback script for '{selected_topic}'.")
                fallback_script = f"""Scene 1:
{selected_topic} is not easy. It takes time. | VISUAL: Character walking slowly looking tired | TEXT: IT TAKES TIME

Scene 2:
Most people give up right before the finish line. | VISUAL: Character sitting on a bench thinking | TEXT: DON'T GIVE UP

Scene 3:
But you are different. You keep pushing forward. | VISUAL: Character standing up and pointing | TEXT: YOU ARE DIFFERENT

Scene 4:
Every single day, you get one step closer. | VISUAL: Character walking bravely | TEXT: ONE STEP CLOSER

Scene 5:
Keep going. Your future depends on it. | VISUAL: Character talking directly to camera | TEXT: KEEP GOING"""
                import datetime
                os.makedirs("scripts", exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                script_file = f"scripts/script_fallback_{timestamp}.txt"
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(fallback_script)

            if not script_file or not os.path.exists(script_file):
                safe_print("❌ [ERROR] Script generation failed. Skipping this video.")
                continue
            safe_print(f"✅ [SCRIPT] Done! Script saved to {script_file}")
        except Exception as e:
            safe_print(f"❌ [ERROR] Script generation failed: {e}")
            continue

        # 3. Generate Voice (Local pyttsx3 fallback or native edge_tts if online)
        safe_print("🎙️ [VOICE] Generating offline voiceover...")
        from voice_agent import generate_voice
        try:
            voice_file = generate_voice(script_file)
            if not voice_file or not os.path.exists(voice_file):
                safe_print("❌ [ERROR] Voice generation failed. Skipping this video.")
                continue
        except Exception as e:
            safe_print(f"❌ [ERROR] Voice generation failed: {e}")
            continue

        # 4. Generate 3D Video (Local Blender & Moviepy)
        safe_print("🎬 [VIDEO] Rendering 3D Animation offline...")
        from video_agent import create_video
        try:
            out_file = create_video(script_file, voice_file, topic_title=selected_topic)
            safe_print(f"✅ [SUCCESS] Offline Video Finished: {out_file}")
        except Exception as e:
            safe_print(f"❌ [ERROR] Video rendering failed: {e}")
            continue
            
    safe_print("\n🏁 [FACTORY] Daily production complete. All assets saved locally.")

if __name__ == "__main__":
    import sys
    if "--test-run" in sys.argv:
        safe_print("Running single test iteration...")
        # Force just 1 execution for the test
        topics = ["The Law of Attraction", "Overcoming Procrastination"]
        selected_topic = random.choice(topics)
        
        from script_agent import generate_script
        from voice_agent import generate_voice
        from video_agent import create_video
        
        script_file = generate_script({"title": selected_topic})
        if script_file:
            voice_file = generate_voice(script_file)
            if voice_file:
                create_video(script_file, voice_file, topic_title=selected_topic)
    else:
        run_offline_automation()
