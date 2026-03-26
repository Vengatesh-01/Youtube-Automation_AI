import os
import sys
import time
import subprocess
import json
import random
import requests

# --- LOGGING SETUP ---
def log_to_file(msg):
    with open("integrated_debug_v2.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

log_to_file("Script starting...")
print("DEBUG: integrated_pipeline.py HAS STARTED")

# --- PATH SETUP ---
PROJECT_ROOT = os.path.abspath(os.getcwd())
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "YouTube_Automation_Free"))
log_to_file(f"Sys.path updated: {str(sys.path[-2:])}")

SADTALKER_DIR = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main"
SADTALKER_INFERENCE = os.path.join(SADTALKER_DIR, "inference.py")
SADTALKER_PYTHON = os.path.join(SADTALKER_DIR, r"venv\Scripts\python.exe")

try:
    log_to_file("Attempting imports...")
    from scripts.ollama_gen import generate_script
    # from generate_animated_background import generate_animated_background 
    # ^ Temporarily disabled to avoid import issues, will inline logic
    from combine_videos import combine
    log_to_file("Imports successful.")
except Exception as e:
    log_to_file(f"Import Error: {e}")
    sys.exit(1)

def text_to_speech(text, output_file):
    print(f"Generating Voice with pyttsx3: {output_file}")
    import pyttsx3
    import re
    speech_text = re.sub(r'\[.*?\]', '', text).strip()
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        for voice in voices:
            if "zira" in voice.name.lower() or "female" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.save_to_file(speech_text, output_file)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"TTS failed: {e}")
        return False
        
def generate_visual_prompt(script):
    """
    Uses Ollama to generate a high-quality visual prompt for AnimateDiff 
    based on the script content.
    """
    msg = "🧠 Generating Smart Visual Prompt with Ollama..."
    print(msg)
    log_to_file(msg)
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"""
        Based on this video script, generate a ONE-SENTENCE visual description for an animated background.
        The description should be abstract, cinematic, and match the mood of the script.
        Focus on colors, motion, and lighting.
        
        SCRIPT:
        {script}
        
        Output ONLY the visual description (max 20 words).
        Example: "Golden particles flowing in a dark void, cinematic lighting, slow motion."
        """,
        "stream": False
    }
    try:
        log_to_file(f"Requesting visual prompt from {url}...")
        response = requests.post(url, json=payload, timeout=15)
        log_to_file(f"Ollama status: {response.status_code}")
        visual_prompt = response.json().get('response', '').strip()
        # Clean up quotes if present
        visual_prompt = visual_prompt.replace('"', '').replace("'", "")
        log_to_file(f"Visual prompt: {visual_prompt}")
        return visual_prompt
    except Exception as e:
        msg = f"Visual prompt generation failed: {e}"
        print(msg)
        log_to_file(msg)
        # Use first line or topic as fallback
        return script.split('.')[0][:100].replace("[", "").replace("]", "").strip()

def run_sadtalker(audio_path, image_path, result_dir):
    print("🚀 Launching SadTalker (FAST Config)...")
    # Using the USER's FAST config
    cmd = [
        SADTALKER_PYTHON, SADTALKER_INFERENCE,
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--result_dir", result_dir,
        "--cpu",
        "--batch_size", "1",
        "--size", "256",
        # "--fps", "18", # Removed because unsupported in this version
        "--expression_scale", "0.9",
        "--pose_style", "0",
        "--still",
        "--preprocess", "crop",
        # "--enhancer", "none", # The script works better without this flag if none are wanted
        # "--background_enhancer", "none",
        # "--face3dvis", "False",
        "--input_yaw", "0",
        "--input_pitch", "0",
        "--input_roll", "0"
    ]
    
    # We will add enhancer none only if the script supports it, 
    # but help suggests just omitting enhancers is the way.
    log_path = os.path.join(PROJECT_ROOT, "integrated_sadtalker.log")
    log_to_file(f"Launching SadTalker. Log: {log_path}")
    try:
        with open(log_path, "w") as f:
            process = subprocess.Popen(cmd, stdout=f, stderr=f, cwd=SADTALKER_DIR)
            process.wait()
        
        log_to_file(f"SadTalker process finished with code {process.returncode}")
        if process.returncode != 0:
            return False
        return True
    except Exception as e:
        log_to_file(f"SadTalker Exception: {e}")
        return False

def run_pipeline(topic):
    # 1. Generate Script
    IS_QUICK = "--quick" in sys.argv
    log_to_file(f"STARTING INTEGRATED PIPELINE (QUICK={IS_QUICK}): {topic}")
    
    timestamp = int(time.time())
    work_dir = os.path.join(PROJECT_ROOT, "outputs", f"run_{timestamp}")
    os.makedirs(work_dir, exist_ok=True)
    log_to_file(f"Work dir created: {work_dir}")
    
    audio_file = os.path.join(work_dir, "voice.wav")
    script_file = os.path.join(work_dir, "script.txt")
    face_image = os.path.abspath("inputs/portrait.png") 
    sadtalker_results = os.path.join(work_dir, "sadtalker")
    bg_video = os.path.join(work_dir, "background.mp4")
    final_video = os.path.join(work_dir, "final_composition.mp4")

    # 1. Generate Script
    log_to_file(f"Step 1: Generating Script for: {topic[:50]}...")
    
    USER_EXAMPLE_SCRIPT = (
        "In 2 years... AI will replace people who don’t adapt.\n\n"
        "Right now, someone with zero money is making lakhs using AI tools.\n"
        "No office. No boss. Just a laptop.\n\n"
        "While others scroll... they build income streams.\n\n"
        "Imagine waking up in a luxury apartment,\n"
        "checking your phone... and money is already coming in.\n\n"
        "That life? It’s not luck. It’s leverage.\n\n"
        "Start using AI today... or get left behind."
    )

    if IS_QUICK:
        script = "AI wealth."
        log_to_file("QUICK MODE: Using short script template.")
    else:
        try:
            if os.path.exists(topic):
                with open(topic, 'r', encoding='utf-8') as f:
                    full_prompt = f.read()
            else:
                full_prompt = topic
                
            script = generate_script(full_prompt)
            if not script or len(script) < 10:
                 script = USER_EXAMPLE_SCRIPT
        except Exception as e:
            log_to_file(f"Script generation error: {e}")
            script = USER_EXAMPLE_SCRIPT
        
    with open(script_file, "w", encoding='utf-8') as f: f.write(script)
    log_to_file("Script saved.")

    # 2. Generate Voice
    log_to_file("Step 2: Generating Voice...")
    if IS_QUICK:
        import shutil
        # Reuse an existing voice file if available or just generate a tiny one
        shutil.copy("YouTube_Automation_Free/outputs/voice.wav", audio_file)
        log_to_file("QUICK MODE: Using mock voice (copying existing).")
    elif not text_to_speech(script, audio_file): 
        log_to_file("Voice generation FAILED.")
        return
    else:
        log_to_file("Voice generation successful.")

    # 3. Generate Animated Background (AnimateDiff)
    log_to_file("Step 3: Generating Animated Background (AnimateDiff)...")
    bg_path = None
    
    # Smarter background matching using Ollama
    if IS_QUICK:
        visual_match = "Abstract cinematic digital wealth, glowing particles, luxurious gold and black"
        log_to_file(f"QUICK MODE: Using hardcoded visual prompt: {visual_match}")
    else:
        visual_match = generate_visual_prompt(script)
    
    bg_prompt = f"{visual_match}, cinematic, high quality, loop, abstract motion"
    log_to_file(f"Target BG Prompt: {bg_prompt}")
    
    COMFY_URL = "http://127.0.0.1:8188"
    def wait_for_server_local(url, timeout=120):
        log_to_file(f"Waiting for ComfyUI at {url}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                r = requests.get(f"{url}/prompt", timeout=2)
                if r.status_code == 200:
                    log_to_file("ComfyUI is ONLINE and READY.")
                    return True
            except:
                pass
            time.sleep(5)
        return False

    if wait_for_server_local(COMFY_URL):
        try:
            # --- INLINED ANIMATEDIFF LOGIC ---
            import uuid
            prompt_id = str(uuid.uuid4())
            num_frames = 4 if IS_QUICK else 8
            
            # Simple workflow for AnimateDiff
            workflow = {
                "1": {"inputs": {"ckpt_name": "dreamshaper_8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
                "2": {"inputs": {"model_name": "mm_sd_v15_v2.ckpt"}, "class_type": "ADE_LoadAnimateDiffModel"},
                "3": {"inputs": {"motion_model": ["2", 0]}, "class_type": "ADE_ApplyAnimateDiffModelSimple"},
                "4": {"inputs": {"model": ["1", 0], "beta_schedule": "autoselect", "m_models": ["3", 0]}, "class_type": "ADE_UseEvolvedSampling"},
                "5": {"inputs": {"text": bg_prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
                "6": {"inputs": {"text": "blurry, low quality, distortion", "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
                "7": {"inputs": {"width": 512, "height": 512, "batch_size": num_frames}, "class_type": "EmptyLatentImage"},
                "8": {"inputs": {"seed": random.randint(0, 10**9), "steps": 15, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0]}, "class_type": "KSampler"},
                "9": {"inputs": {"samples": ["8", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
                "10": {"inputs": {"images": ["9", 0], "frame_rate": 8, "loop_count": 0, "filename_prefix": "AD_Auto", "format": "video/h264-mp4", "save_output": True}, "class_type": "VHS_VideoCombine"}
            }
            
            log_to_file("Queueing AnimateDiff job...")
            resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
            if resp.status_code == 200:
                comfy_prompt_id = resp.json().get("prompt_id")
                log_to_file(f"Job Queued! ID: {comfy_prompt_id}")
                
                # Poll for completion
                start_poll = time.time()
                while time.time() - start_poll < 600: # 10 min max for quick test
                    time.sleep(10)
                    h_resp = requests.get(f"{COMFY_URL}/history/{comfy_prompt_id}", timeout=10)
                    if h_resp.status_code == 200:
                        history = h_resp.json()
                        if comfy_prompt_id in history:
                            log_to_file("AnimateDiff generation COMPLETE.")
                            # Extract filename (simplified)
                            outputs = history[comfy_prompt_id].get("outputs", {})
                            for node_id in outputs:
                                if "videos" in outputs[node_id]:
                                    filename = outputs[node_id]["videos"][0]["filename"]
                                    # Download
                                    log_to_file(f"Downloading {filename}...")
                                    v_resp = requests.get(f"{COMFY_URL}/view", params={"filename": filename, "type": "output"}, timeout=60)
                                    with open(bg_video, "wb") as f: f.write(v_resp.content)
                                    bg_path = bg_video
                                    break
                            if bg_path: break
                if not bg_path: log_to_file("AnimateDiff polling TIMEOUT.")
            else:
                log_to_file(f"Queue Error {resp.status_code}: {resp.text}")
        except Exception as e:
            log_to_file(f"AnimateDiff Inline Error: {e}")
    else:
        log_to_file("AnimateDiff Skip: ComfyUI server not responding after wait.")

    if not bg_path:
        log_to_file("AnimateDiff FAILED or server DOWN, using fallback.")
        # Try to find any existing AD result or use a stock one
        bg_path = os.path.abspath("YouTube_Automation_Free/outputs/AnimateDiff_FuturisticCity_00001.mp4")
    else:
        import shutil
        shutil.move(bg_path, bg_video)
        bg_path = bg_video
        log_to_file("Background moved to work dir.")

    # 4. Generate SadTalker Head
    log_to_file("Step 4: Generating Talking Head...")
    if not run_sadtalker(audio_file, face_image, sadtalker_results): 
        log_to_file("SadTalker FAILED.")
        return
    log_to_file("SadTalker finished.")
    
    # Find the generated mp4
    import glob
    face_videos = glob.glob(os.path.join(sadtalker_results, "**", "*.mp4"), recursive=True)
    if not face_videos:
        log_to_file("Could not find SadTalker output video.")
        return
    face_video_path = face_videos[0]
    log_to_file(f"Face video found: {face_video_path}")

    # 5. Combine everything
    log_to_file("Step 5: Compositing Final Video...")
    try:
        combine(face_video_path, bg_path, final_video, mode="FINAL", audio_path=audio_file)
        log_to_file(f"SUCCESS! Final video: {final_video}")
        print(f"\n🎉 SUCCESS! Final video: {final_video}")
    except Exception as e:
        log_to_file(f"Compositing failed: {e}")
        return

    # 6. Optional YouTube Upload
    if "--upload" in sys.argv:
        log_to_file("Step 6: Attempting YouTube Upload...")
        from upload_agent import upload_video
        
        # Extract metadata from args or use defaults
        title = topic.title()
        description = f"Automated cinematic video about {topic}.\n\n#automation #ai #video"
        publish_at = None
        
        # Find --publish_at in sys.argv
        for i, arg in enumerate(sys.argv):
            if arg == "--publish_at" and i + 1 < len(sys.argv):
                publish_at = sys.argv[i+1]
        
        try:
            url = upload_video(
                video_file=final_video,
                title=title,
                description=description,
                publish_at=publish_at
            )
            if url:
                log_to_file(f"YouTube Upload successful: {url}")
            else:
                log_to_file("YouTube Upload skipped (no credentials).")
        except Exception as e:
            log_to_file(f"YouTube Upload Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python integrated_pipeline.py <topic> [--upload] [--publish_at 2026-03-25T10:00:00Z]")
        sys.exit(0)
        
    topic = sys.argv[1]
    run_pipeline(topic)
