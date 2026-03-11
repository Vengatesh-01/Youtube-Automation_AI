import os
import sys
import json
import traceback

def check_imports():
    print("--- [Health Check] Testing Imports ---")
    try:
        import topic_agent
        import script_agent
        import voice_agent
        import thumbnail_agent
        from video_agent.video_agent import create_video
        import upload_agent
        print("✅ All automation modules imported successfully.")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    return True

def check_files():
    print("\n--- [Health Check] Testing Files & Directories ---")
    required_files = ["client_secrets.json", "main.py"]
    required_dirs = ["videos", "thumbnails", "scripts", "topics", "voiceovers"]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    for d in required_dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"📁 Created missing directory: {d}")
            
    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        if "client_secrets.json" in missing:
            print("   (Note: client_secrets.json is required for YouTube upload)")
        return False
    
    if os.path.exists("token.json"):
        print("✅ token.json found (YouTube session exists).")
    else:
        print("⚠️  token.json NOT found. Manual authentication will be required for uploads.")
        
    return True

def check_ffmpeg():
    print("\n--- [Health Check] Testing FFmpeg ---")
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"✅ FFmpeg found at: {ffmpeg_path}")
    else:
        print("❌ FFmpeg NOT found. Video rendering will fail.")
        return False
    return True

def run_health_check():
    print("==========================================")
    print("   YouTube Automation System Health Check")
    print("==========================================\n")
    
    results = [
        check_imports(),
        check_files(),
        check_ffmpeg()
    ]
    
    print("\n==========================================")
    if all(results):
        print("🚀 SYSTEM READY: All checks passed!")
        sys.exit(0)
    else:
        print("❌ SYSTEM ISSUES: Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    run_health_check()
