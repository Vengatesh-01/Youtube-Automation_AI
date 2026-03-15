import subprocess
import os
import sys
import time

BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
CHARACTER_BLEND = os.path.join("assets", "character.blend")
GENERATOR_SCRIPT = "blender_shorts_generator.py"
OUTPUT_VIDEO = os.path.join("outputs", "cartoon_short.mp4")

def test_blender_connection():
    print("--- Blender Automation Pipeline Verification ---")
    
    # 1. Existence Checks
    checks = [
        ("Blender Executable", BLENDER_PATH),
        ("Character Blend File", CHARACTER_BLEND),
        ("Generator Script", GENERATOR_SCRIPT)
    ]
    
    all_passed = True
    for name, path in checks:
        if os.path.exists(path):
            print(f"[OK] {name} found at: {path}")
        else:
            print(f"[FAIL] {name} NOT FOUND at: {path}")
            all_passed = False
            
    if not all_passed:
        print("\nERROR: Verification failed during existence checks. Please fix the paths above.")
        return

    # 2. Preparation: Remove old output if exists
    if os.path.exists(OUTPUT_VIDEO):
        try:
            os.remove(OUTPUT_VIDEO)
            print(f"[INFO] Removed existing output: {OUTPUT_VIDEO}")
        except Exception as e:
            print(f"[WARNING] Could not remove existing output: {e}")

    # 3. Execution
    print("\nLaunching Blender in background mode...")
    cmd = [
        BLENDER_PATH,
        "-b", CHARACTER_BLEND,
        "-P", GENERATOR_SCRIPT
    ]
    
    # We set environment variables to ensure the generator script has what it needs
    # even in a minimal test environment.
    env = os.environ.copy()
    if "SHORTS_TOPIC" not in env:
        env["SHORTS_TOPIC"] = "Blender Connectivity Test"
    env["TOTAL_SEC"] = "2" # 2 seconds = 60 frames
    
    start_time = time.time()
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        
        # Stream output in real-time
        for line in process.stdout:
            print(f"  [Blender] {line.strip()}")
            
        process.wait()
        duration = time.time() - start_time
        
        if process.returncode == 0:
            print(f"\n[OK] Blender finished successfully in {duration:.2f}s.")
        else:
            print(f"\n[FAIL] Blender exited with error code {process.returncode} after {duration:.2f}s.")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to launch Blender: {e}")
        return

    # 4. Final Verification
    if os.path.exists(OUTPUT_VIDEO):
        file_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
        print(f"[SUCCESS] Render output created: {OUTPUT_VIDEO} ({file_size:.2f} MB)")
    else:
        print(f"[FAIL] Render output NOT CREATED at: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    test_blender_connection()
