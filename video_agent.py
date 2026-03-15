import os
import subprocess
import random
from datetime import datetime
from utils import safe_print

def log_agent(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [VideoAgent] {msg}"
    safe_print(log_line)
    os.makedirs("videos", exist_ok=True)
    with open("videos/automation.log", "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
GENERATOR_SCRIPT = os.path.abspath("blender_shorts_generator.py")
CHARACTER_BLEND = os.path.abspath("assets/character.blend")

def create_video(script_path: str, voice_file: str, topic_title: str = "Never Give Up", video_segments: list = []) -> str:
    """
    Directly calls the Blender Shorts Generator.
    Passes local video segments for assembly.
    """
    log_agent(f"🚀 Starting Local Blender Assembly for: {topic_title}")
    
    # Define output path
    os.makedirs("outputs", exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    output_filename = f"local_short_{ts}.mp4"
    output_path = os.path.abspath(os.path.join("outputs", output_filename))

    TEMPLATE_PATH = os.path.abspath("assets/shorts_template.blend")
    BASE_BLEND = TEMPLATE_PATH if os.path.exists(TEMPLATE_PATH) else os.path.abspath("assets/character.blend")

    # Prepare environment for Blender script
    env = os.environ.copy()
    env["SHORTS_AUDIO"] = os.path.abspath(voice_file)
    env["SHORTS_TOPIC"] = topic_title
    env["SHORTS_OUTPUT"] = output_path
    env["VIDEO_SEGMENTS"] = ",".join([os.path.abspath(s) for s in video_segments])
    
    # Reset TOTAL_SEC if it was set for testing, so we get full length
    env.pop("TOTAL_SEC", None)

    cmd = [
        BLENDER_EXE,
        "-b", BASE_BLEND,
        "-P", GENERATOR_SCRIPT
    ]

    log_agent(f"🎬 [BLENDER] Launching renderer...")
    try:
        # Run Blender in background
        process = subprocess.run(
            cmd, 
            env=env,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            check=False
        )
        
        # Save logs
        with open("blender_render.log", "w", encoding="utf-8") as f:
            f.write(process.stdout)
            if process.stderr:
                f.write("\n--- ERRORS ---\n")
                f.write(process.stderr)

        if process.returncode != 0:
            log_agent(f"❌ [ERROR] Blender exited with code {process.returncode}")
            return ""

        if os.path.exists(output_path):
            log_agent(f"✅ [SUCCESS] Video generated: {output_path}")
            
            # Optionally move to 'videos' folder for final consistency with the rest of the app
            final_dir = "videos"
            os.makedirs(final_dir, exist_ok=True)
            final_path = os.path.join(final_dir, output_filename)
            import shutil
            shutil.move(output_path, final_path)
            return final_path
        else:
            # Check if it rendered PNG sequence instead (fallback)
            png_fallback = os.path.join("outputs", "frame_0001.png")
            if os.path.exists(png_fallback):
                log_agent("⚠️ [WARNING] Video was rendered as a PNG sequence due to codec availability.")
                return f"outputs/frame_ (PNG Sequence)"
            
            log_agent("❌ [ERROR] Blender finished but output file was not found.")
            return ""

    except Exception as e:
        log_agent(f"❌ [CRITICAL] Subprocess failed: {e}")
        return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        create_video(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Never Give Up")
