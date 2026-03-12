import os
import sys
from script_agent import generate_script
from voice_agent import generate_voice
from video_agent import create_video

# Add local path to ensure imports work if needed
sys.path.append(os.getcwd())

import traceback

def verify():
    try:
        print("[VERIFICATION] Starting Cinematic Producer Test...")
        
        script_path = "cinematic_test.txt"
        if not os.path.exists(script_path):
            print(f"Error: {script_path} not found.")
            return

        # Bypass TTS to avoid network issues for this test
        voice_file = r"voiceovers\voiceover_20260312_214223.mp3"
        if not os.path.exists(voice_file):
            # Fallback if specific file missing
            files = sorted([f for f in os.listdir("voiceovers") if f.endswith(".mp3")], reverse=True)
            if files: voice_file = os.path.join("voiceovers", files[0])
        
        print(f"[VERIFICATION] Using existing voice file: {voice_file}")
        
        print(f"[VERIFICATION] Rendering video with cinematic markers...")
        video_file = create_video(script_path, voice_file, "Cinematic Test")
        
        print(f"[VERIFICATION] Success! Video ready at: {video_file}")
    except Exception:
        with open("traceback.log", "w") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()

if __name__ == "__main__":
    verify()
