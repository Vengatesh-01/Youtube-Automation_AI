import os
import sys
import time
import subprocess
import json
import requests

# --- CONFIGURATION ---
SADTALKER_DIR = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main"
SADTALKER_INFERENCE = os.path.join(SADTALKER_DIR, "inference.py")
SADTALKER_PYTHON = os.path.join(SADTALKER_DIR, r"venv\Scripts\python.exe")

PROJECT_VENV_PYTHON = os.path.abspath(r"YouTube_Automation_Free\venv\Scripts\python.exe")

OLLAMA_URL = "http://localhost:11434/api/generate"
# COMFY_URL = "http://127.0.0.1:8188/generate" # From comfy_gen.py
# However, the user also mentioned 127.0.0.1:7860 which might be a WebUI.
# We will use the existing scripts where possible.

# Ensure directories exist
for d in ["inputs", "outputs", "results"]:
    os.makedirs(d, exist_ok=True)

# Import existing scripts
sys.path.append(os.getcwd())
try:
    from scripts.ollama_gen import generate_script
    # We will use our own TTS logic matching voice_agent.py
    # from scripts.piper_tts
    from scripts.comfy_gen import generate_content
except ImportError as e:
    print(f"Error importing scripts: {e}")
    sys.exit(1)

import pyttsx3 # Moved pyttsx3 import to top-level for consistency

def text_to_speech_pyttsx3(text, output_file):
    print(f"Generating Voice with pyttsx3: {output_file}")
    import pyttsx3
    import re
    speech_text = re.sub(r'\[.*?\]', '', text).strip()
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 155)
        engine.setProperty('volume', 0.95)
        
        voices = engine.getProperty('voices')
        # Priority for high-quality female voices on Windows (Zira is default, but others might exist)
        selected_voice = None
        for voice in voices:
            v_name = voice.name.lower()
            # Look for specific natural-sounding female voices if installed
            if any(k in v_name for k in ('zira', 'aria', 'jenny', 'samantha', 'victoria')):
                selected_voice = voice.id
                break
        
        if selected_voice:
            engine.setProperty('voice', selected_voice)
        
        engine.save_to_file(speech_text, output_file)
        engine.runAndWait()
        print(f"Audio generated: {output_file}")
        return True
    except Exception as e:
        print(f"pyttsx3 failed: {e}")
        return False

def run_sadtalker_inference(audio_path, image_path, result_dir="./results"):
    print(" Launching SadTalker Video Generation...")
    
    cmd = [
        SADTALKER_PYTHON, SADTALKER_INFERENCE,
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--result_dir", result_dir,
        "--cpu",
        "--batch_size", "1",
        "--size", "256",
        "--fps", "18",
        "--expression_scale", "0.9",
        "--pose_style", "0",
        "--still",
        "--preprocess", "crop",
        "--enhancer", "none",
        "--background_enhancer", "none",
        "--face3dvis", "False",
        "--input_yaw", "0",
        "--input_pitch", "0",
        "--input_roll", "0"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    try:
        # We need to run this in the SadTalker directory or ensure it finds its checkpoints
        result = subprocess.run(cmd, check=True, cwd=SADTALKER_DIR, capture_output=True, text=True)
        print(f"SadTalker rendering complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"SadTalker failed: {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        return False

def get_background_prompt(topic, script):
    """
    Returns a fitting background description. 
    Mocked to a high-quality professional default to avoid Ollama dependency/hangs.
    """
    return "modern office / glass interior"

def run_pipeline(topic, audio_path=None, script_path=None, image_path=None):
    print(f"INITIALIZING SADTALKER PIPELINE: {topic}")
    
    audio_file = os.path.abspath(audio_path) if audio_path else os.path.abspath("inputs/voice.wav")
    image_file = os.path.abspath(image_path) if image_path else os.path.abspath("inputs/portrait.png")
    script_file = os.path.abspath(script_path) if script_path else os.path.abspath("inputs/script.txt")
    
    # 1. SCRIPT GENERATION
    if not script_path:
        print("Generating Script...")
        script = generate_script(topic)
        if not script:
            print("Script generation failed.")
            return False
        
        with open(script_file, "w") as f:
            f.write(script)
        print(f"--- SCRIPT SAVED TO {script_file} ---")
        print(f"{script}\n----------------------------")
    else:
        print(f" Using existing script: {script_file}")
        with open(script_file, "r") as f:
            script = f.read()

    # 2. VOICE TTS
    if not audio_path:
        print("Generating Voice...")
        if not text_to_speech_pyttsx3(script, audio_file):
            print("TTS failed.")
            return False
    else:
        print(f"Using existing audio: {audio_file}")

    # 3. IMAGE GENERATION
    if not image_path:
        with open("debug_flow.log", "a") as f: f.write("Entering IMAGE GENERATION stage...\n")
        print("Generating High-Quality Portrait Image...")
        
        bg_desc = get_background_prompt(topic, script)
        with open("debug_flow.log", "a") as f: f.write(f"Background description: {bg_desc}\n")
        
        portrait_prompt = f"""
        A highly realistic, beautiful modern young woman, close-up portrait, ultra-detailed face, natural skin texture, 
        soft glowing skin, expressive eyes, perfectly shaped lips with accurate lip sync, subtle smile, 
        confident and elegant expression. Stylish appearance with trendy fashion (visible upper outfit: modern jacket or chic top), 
        neat hair with soft natural movement, slightly glossy lips, well-defined eyebrows, cinematic makeup look. 
        Lighting is soft and cinematic: warm key light on face, gentle shadows, subtle rim light for depth, DSLR quality, 
        shallow depth of field, background is {bg_desc} softly blurred (bokeh effect). 
        Natural micro-expressions: blinking, slight head movement, subtle breathing, smooth facial motion. 
        Perfect facial alignment for lip sync, stable face, no distortion, high temporal consistency. 
        Style: hyper-realistic, cinematic, slightly stylized beauty enhancement, not cartoonish.
        Camera: static or very subtle cinematic movement, focused on face.
        """.strip()

        negative_prompt = "low quality, blurry, distorted face, bad anatomy, extra eyes, extra lips, asymmetrical face, cartoon, anime, overexposed, underexposed, flickering, jitter, unstable face, bad lip sync, open mouth freeze, warped features"

        with open("debug_flow.log", "a") as f: f.write(f"Calling generate_content for portrait with file: {image_file}\n")
        if not generate_content(portrait_prompt, image_file, type="portrait", negative_prompt=negative_prompt):
            with open("debug_flow.log", "a") as f: f.write("generate_content FAILED\n")
            print("Image generation failed.")
            return False
        with open("debug_flow.log", "a") as f: f.write("generate_content SUCCESS\n")
    else:
        print(f"Using existing image: {image_file}")

    # 4. VIDEO GENERATION (SadTalker)
    if not run_sadtalker_inference(audio_file, image_file):
        print("Video generation failed.")
        return False

    print("PIPELINE COMPLETED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SadTalker Automated Pipeline")
    parser.add_argument("--topic", type=str, default="motivation", help="Topic for the script")
    parser.add_argument("--audio", type=str, help="Path to existing audio file")
    parser.add_argument("--script", type=str, help="Path to existing script file")
    parser.add_argument("--image", type=str, help="Path to existing image file")
    args = parser.parse_args()
    
    run_pipeline(args.topic, args.audio, args.script, args.image)
