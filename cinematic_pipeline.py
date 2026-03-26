"""
cinematic_pipeline.py  —  CINEMATIC AVATAR VIDEO GENERATOR
===========================================================
Creates hyper-realistic vertical (9:16) talking-head videos for
YouTube Shorts / Instagram Reels.

Pipeline:
  1. Script Generation  → Ollama (llama3) with scene-type detection
  2. Voice TTS          → pyttsx3 (Zira female voice, natural pacing)
  3. Portrait Gen       → ComfyUI (ultra-realistic, SadTalker-optimized)
  4. AnimateDiff BG     → ComfyUI scene-matched cinematic background
  5. SadTalker          → Lip-synced talking head
  6. FFmpeg Composite   → 1080x1920 vertical, cinematic grading
  7. YouTube Upload     → Optional scheduled upload

Usage:
  python cinematic_pipeline.py "AI wealth mindset"
  python cinematic_pipeline.py "AI wealth mindset" --upload
  python cinematic_pipeline.py "AI wealth mindset" --upload --publish_at 2026-03-26T10:00:00Z
  python cinematic_pipeline.py --quick     (fast test run)
"""

import os, sys, time, subprocess, json, random, glob, shutil, re, uuid
import requests
from typing import Optional

# Force UTF-8 for Windows console (solves emoji UnicodeEncodeError)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ── PATH SETUP ──────────────────────────────────────────────────────────────
PROJECT_ROOT      = os.path.abspath(os.getcwd())
SADTALKER_DIR     = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main"
SADTALKER_PYTHON  = os.path.join(SADTALKER_DIR, r"venv\Scripts\python.exe")
SADTALKER_INFER   = os.path.join(SADTALKER_DIR, "inference.py")
COMFY_URL         = "http://127.0.0.1:8188"
OLLAMA_URL        = "http://127.0.0.1:11434/api/generate"
FFMPEG_EXE        = r"C:\ffmpeg\bin\ffmpeg.exe"   # adjust if needed
if not os.path.isfile(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg"   # fallback to PATH

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "YouTube_Automation_Free"))

LOG_FILE = os.path.join(PROJECT_ROOT, "cinematic_run.log")

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── SCENE DETECTION ─────────────────────────────────────────────────────────
SCENE_BACKGROUNDS = {
    "motivation": {
        "bg": "sunrise city skyline golden hour, success atmosphere, bokeh background, cinematic, subtle motion, lighting movement, environment depth",
        "color_grade": "warm golden, high contrast",
    },
    "tech": {
        "bg": "futuristic workspace glowing screens, neon blue text accents, dark ambient, modern environment, bokeh background, cinematic, subtle motion, lighting movement, environment depth",
        "color_grade": "cool teal, neon highlights",
    },
    "casual": {
        "bg": "cozy aesthetic room warm ambient candlelight bokeh, soft cream tones, hygge interior, cinematic, subtle motion, lighting movement, environment depth",
        "color_grade": "warm cream, soft shadows",
    },
    "lifestyle": {
        "bg": "golden sunset outdoor cafe terrace street, warm bokeh fairy lights, ambient street activity, cinematic, subtle motion, lighting movement, environment depth",
        "color_grade": "golden hour, vivid tones",
    },
}

SCENE_KEYWORDS = {
    "motivation": ["motivat", "success", "wealth", "money", "rich", "grind", "hustle",
                   "mindset", "goal", "dream", "win", "grow", "ambition", "power", "ai"],
    "tech":       ["tech", "ai", "coding", "software", "dev", "digital", "cyber",
                   "data", "machine", "robot", "python", "future", "innovation"],
    "casual":     ["morning", "coffee", "daily", "routine", "life", "relax", "home",
                   "self care", "tips", "hack", "productivity"],
    "lifestyle":  ["travel", "food", "fashion", "fitness", "gym", "yoga", "luxury",
                   "explore", "adventure", "outdoor", "sunset", "café"],
}

def detect_scene(topic: str, script: str = "") -> str:
    text = (topic + " " + script).lower()
    scores = {scene: 0 for scene in SCENE_KEYWORDS}
    for scene, kws in SCENE_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[scene] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "motivation"

# ── SCRIPT GENERATION ───────────────────────────────────────────────────────
FALLBACK_SCRIPT = (
    "In 2 years... AI will replace those who don't adapt.\n\n"
    "Someone with zero money is making lakhs using AI tools.\n"
    "No office. No boss. Just a laptop.\n\n"
    "While others scroll... they build income streams.\n\n"
    "That life? It's not luck. It's leverage.\n\n"
    "Start using AI today... or get left behind."
)

def generate_script(topic: str) -> str:
    log(f"📝 Generating script for: {topic[:60]}")
    payload = {
        "model": "llama3",
        "prompt": f"""
Act as a viral YouTube Shorts script strategist.
Write a 20-40 second motivational/engaging short video script about: {topic}

RULES:
- Script MUST be short and engaging (20-40 seconds of speaking).
- Strong hook in the first 3 seconds (must grab attention).
- Clear message and a satisfying ending/mic-drop statement.
- Use "..." for dramatic pauses to control pacing.
- Output ONLY the spoken words, NO labels, NO stage directions.

TOPIC: {topic}
""",
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        script = r.json().get("response", "").strip()
        # Strip AI preambles
        lines = script.split("\n")
        if lines and (":" in lines[0] or "script" in lines[0].lower()):
            script = "\n".join(lines[1:]).strip()
        if len(script) > 20:
            log(f"✅ Script generated ({len(script)} chars)")
            return script
    except Exception as e:
        log(f"⚠️  Ollama error: {e} — using fallback script")
    return FALLBACK_SCRIPT

# ── TEXT-TO-SPEECH ───────────────────────────────────────────────────────────
def text_to_speech(text: str, output_wav: str) -> bool:
    log(f"🎙️  Generating voice → {os.path.basename(output_wav)}")
    import pyttsx3
    speech = re.sub(r'\[.*?\]', '', text).strip()
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 155)
        engine.setProperty('volume', 1.0)
        for v in engine.getProperty('voices'):
            if any(k in v.name.lower() for k in ('zira', 'aria', 'jenny', 'samantha')):
                engine.setProperty('voice', v.id)
                log(f"   Voice selected: {v.name}")
                break
        engine.save_to_file(speech, output_wav)
        engine.runAndWait()
        if os.path.isfile(output_wav) and os.path.getsize(output_wav) > 1000:
            log(f"✅ Voice saved ({os.path.getsize(output_wav)//1024} KB)")
            return True
    except Exception as e:
        log(f"❌ TTS failed: {e}")
    return False

# ── COMFYUI HELPERS ──────────────────────────────────────────────────────────
def wait_for_comfy(timeout=120) -> bool:
    log(f"⏳ Waiting for ComfyUI at {COMFY_URL}...")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f"{COMFY_URL}/system_stats", timeout=3)
            if r.status_code == 200:
                log("✅ ComfyUI online")
                return True
        except:
            pass
        time.sleep(5)
    log("❌ ComfyUI not responding")
    return False

def comfy_queue(workflow: dict) -> Optional[str]:
    try:
        r = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
        if r.status_code == 200:
            pid = r.json().get("prompt_id")
            log(f"   Queued prompt ID: {pid}")
            return pid
    except Exception as e:
        log(f"❌ Queue error: {e}")
    return None

def comfy_poll(prompt_id: str, timeout=600, interval=8) -> Optional[dict]:
    log(f"⏳ Polling ComfyUI for {prompt_id}...")
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(interval)
        try:
            r = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if r.status_code == 200:
                hist = r.json()
                if prompt_id in hist:
                    log("✅ ComfyUI job complete")
                    return hist[prompt_id].get("outputs", {})
        except Exception as e:
            log(f"   Poll error: {e}")
    log("❌ ComfyUI poll timeout")
    return None

def comfy_download_image(filename: str, dest: str) -> bool:
    try:
        r = requests.get(f"{COMFY_URL}/view", params={"filename": filename, "type": "output"}, timeout=60)
        with open(dest, "wb") as f:
            f.write(r.content)
        log(f"✅ Image downloaded → {os.path.basename(dest)}")
        return True
    except Exception as e:
        log(f"❌ Download error: {e}")
        return False

def comfy_download_video(filename: str, dest: str) -> bool:
    try:
        r = requests.get(f"{COMFY_URL}/view", params={"filename": filename, "type": "output"}, timeout=120)
        with open(dest, "wb") as f:
            f.write(r.content)
        log(f"✅ Video downloaded → {os.path.basename(dest)}")
        return True
    except Exception as e:
        log(f"❌ Download error: {e}")
        return False

# ── PORTRAIT GENERATION (ComfyUI) ────────────────────────────────────────────
PORTRAIT_NEGATIVE = (
    "low quality, blurry, cartoon, anime, unrealistic skin, deformed face, bad anatomy, extra limbs, "
    "stiff motion, frozen pose, extreme head movement, side face, occluded face, flickering, jitter, "
    "unstable frames, morphing face, bad lip sync, open mouth freeze, distorted hands, oversharpen, oversaturated"
)

def generate_portrait_comfy(scene: str, output_path: str) -> bool:
    bg_desc = SCENE_BACKGROUNDS[scene]["bg"].split(",")[0]
    prompt = (
    prompt = (
        f"Subject: highly photorealistic young woman age 25, natural skin texture soft glowing complexion, "
        f"expressive eyes realistic eyelashes well-defined eyebrows, perfectly shaped lips, confident friendly influencer presence, "
        f"subtle smile natural micro-expressions. "
        f"Framing: frontal face centered clearly visible medium close-up upper-body shot, natural posture, no distortion. "
        f"Appearance: modern stylish outfit trendy top jacket clean aesthetic, realistic dark hair soft motion, natural cinematic makeup. "
        f"Environment: {bg_desc} bokeh soft blur cinematic context-aware. "
        f"Lighting/Camera: professional cinematic lighting soft key light on face, rim light depth separation, "
        f"realistic shadows HDR DSLR-quality rendering face clearly illuminated, stable framing, perfectly aligned for lip sync SadTalker. "
        f"Style: hyper-realistic film-grade 8k quality, vertical 9:16 portrait. not cartoon not anime."
    )
    workflow = {
        "1": {"inputs": {"ckpt_name": "dreamshaper_8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "2": {"inputs": {"text": prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "3": {"inputs": {"text": PORTRAIT_NEGATIVE, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "4": {"inputs": {"width": 512, "height": 896, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "5": {
            "inputs": {
                "seed": random.randint(0, 10**9), "steps": 30,
                "cfg": 7.5, "sampler_name": "dpm_2_ancestral",
                "scheduler": "karras", "denoise": 1,
                "model": ["1", 0], "positive": ["2", 0],
                "negative": ["3", 0], "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "6": {"inputs": {"samples": ["5", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
        "7": {"inputs": {"images": ["6", 0], "filename_prefix": "CinematicPortrait"}, "class_type": "SaveImage"},
    }
    pid = comfy_queue(workflow)
    if not pid:
        return False
    outputs = comfy_poll(pid, timeout=900)
    if not outputs:
        return False
    for nid, out in outputs.items():
        if "images" in out:
            return comfy_download_image(out["images"][0]["filename"], output_path)
    return False

# ── ANIMATEDIFF BACKGROUND ────────────────────────────────────────────────────
def generate_background_comfy(scene: str, output_path: str, num_frames=16) -> bool:
    bg_data = SCENE_BACKGROUNDS[scene]
    bg_prompt = (
        f"{bg_data['bg']}, cinematic motion, subtle ambient background animation, environment depth, "
        f"mostly stable camera, very slow push-in, smooth natural transition, "
        f"high quality, atmospheric, depth of field, film grade, looping"
    )
    neg = "static, frozen, blurry, low quality, jitter, flickering, distortion, sudden movements"
    workflow = {
        "1": {"inputs": {"ckpt_name": "dreamshaper_8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "2": {"inputs": {"model_name": "mm_sd_v15_v2.ckpt"}, "class_type": "ADE_LoadAnimateDiffModel"},
        "3": {"inputs": {"motion_model": ["2", 0]}, "class_type": "ADE_ApplyAnimateDiffModelSimple"},
        "4": {"inputs": {"model": ["1", 0], "beta_schedule": "autoselect", "m_models": ["3", 0]}, "class_type": "ADE_UseEvolvedSampling"},
        "5": {"inputs": {"text": bg_prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "6": {"inputs": {"text": neg, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"width": 512, "height": 896, "batch_size": num_frames}, "class_type": "EmptyLatentImage"},
        "8": {
            "inputs": {
                "seed": random.randint(0, 10**9), "steps": 20, "cfg": 7.5,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
                "model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0],
                "latent_image": ["7", 0]
            },
            "class_type": "KSampler"
        },
        "9": {"inputs": {"samples": ["8", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
        "10": {
            "inputs": {
                "images": ["9", 0], "frame_rate": 24, "loop_count": 0,
                "filename_prefix": "CineBG", "format": "video/h264-mp4", "save_output": True
            },
            "class_type": "VHS_VideoCombine"
        }
    }
    pid = comfy_queue(workflow)
    if not pid:
        return False
    outputs = comfy_poll(pid, timeout=1200)
    if not outputs:
        return False
    for nid, out in outputs.items():
        if "videos" in out:
            return comfy_download_video(out["videos"][0]["filename"], output_path)
    return False

# ── SADTALKER ─────────────────────────────────────────────────────────────────
def run_sadtalker(audio: str, image: str, result_dir: str) -> Optional[str]:
    log("🎭 Launching SadTalker lip-sync...")
    os.makedirs(result_dir, exist_ok=True)
    cmd = [
        SADTALKER_PYTHON, SADTALKER_INFER,
        "--driven_audio",   audio,
        "--source_image",   image,
        "--result_dir",     result_dir,
        "--cpu",
        "--batch_size",     "1",
        "--size",           "256",
        "--expression_scale", "0.9",
        "--pose_style",     "0",
        "--still",
        "--preprocess",     "crop",
        "--input_yaw",      "0",
        "--input_pitch",    "0",
        "--input_roll",     "0",
    ]
    sadtalker_log = os.path.join(PROJECT_ROOT, "sadtalker_cinematic.log")
    try:
        with open(sadtalker_log, "w") as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=f, cwd=SADTALKER_DIR)
            proc.wait(timeout=3600)
        if proc.returncode != 0:
            log(f"❌ SadTalker exit code {proc.returncode}. See sadtalker_cinematic.log")
            return None
    except Exception as e:
        log(f"❌ SadTalker exception: {e}")
        return None

    # Find output video
    vids = glob.glob(os.path.join(result_dir, "**", "*.mp4"), recursive=True)
    if vids:
        log(f"✅ SadTalker output: {vids[0]}")
        return vids[0]
    log("❌ SadTalker: no output mp4 found")
    return None

# ── FFMPEG COMPOSITING ───────────────────────────────────────────────────────
def compose_vertical(face_vid: str, bg_vid: str, audio: str, out_path: str) -> bool:
    """
    Composes final 9:16 (1080×1920) vertical video:
      - Background scaled/cropped to 1080×1920
      - Face video scaled to ~540px wide, centered
      - Cinematic color grading (curves, saturation, vignette)
      - Audio from TTS merged
    """
    log(f"🎬 Compositing final video → {os.path.basename(out_path)}")
    # Face video scaled to 60% width centered, placed at vertical center
    face_w = 648   # ~60% of 1080
    face_h = int(face_w * 4 / 3)   # 4:3 face
    ox = (1080 - face_w) // 2      # center x
    oy = (1920 - face_h) // 2      # center y

    filter_complex = (
        # BG: scale+crop to 1080x1920
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"boxblur=4:1[bg];"
        # Face: scale, ensure alpha
        f"[1:v]scale={face_w}:{face_h}:force_original_aspect_ratio=decrease,"
        f"pad={face_w}:{face_h}:(ow-iw)/2:(oh-ih)/2:black[face_scaled];"
        # Overlay face on BG, centered
        f"[bg][face_scaled]overlay={ox}:{oy}:shortest=1[comp];"
        # Cinematic grade: warm lut-style, slight vignette
        f"[comp]eq=brightness=0.02:saturation=1.15:contrast=1.1,"
        f"vignette=PI/4[out]"
    )

    cmd = [
        FFMPEG_EXE, "-y",
        "-stream_loop", "-1",
        "-i", bg_vid,
        "-i", face_vid,
        "-i", audio,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        out_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and os.path.isfile(out_path):
            size_mb = os.path.getsize(out_path) / (1024*1024)
            log(f"✅ Final video: {out_path} ({size_mb:.1f} MB)")
            return True
        else:
            log(f"❌ FFmpeg error:\n{result.stderr[-1000:]}")
            return False
    except Exception as e:
        log(f"❌ FFmpeg exception: {e}")
        return False

def compose_portrait_only(face_vid: str, audio: str, out_path: str) -> bool:
    """Fallback: no BG, just scale face to 1080×1920."""
    log("🎬 Fallback compose (no BG)...")
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", face_vid,
        "-i", audio,
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            "eq=brightness=0.02:saturation=1.1:contrast=1.08,"
            "vignette=PI/4"
        ),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest", out_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and os.path.isfile(out_path):
            log(f"✅ Portrait-only output: {out_path}")
            return True
        log(f"❌ Fallback compose failed:\n{result.stderr[-500:]}")
        return False
    except Exception as e:
        log(f"❌ Fallback compose exception: {e}")
        return False

# ── YOUTUBE UPLOAD ────────────────────────────────────────────────────────────
def upload_to_youtube(video_path: str, title: str, description: str, publish_at: Optional[str] = None):
    try:
        sys.path.append(os.path.join(PROJECT_ROOT, "YouTube_Automation_Free"))
        from upload_agent import upload_video
        url = upload_video(video_path, title, description, publish_at=publish_at)
        if url:
            log(f"🚀 Uploaded: {url}")
        else:
            log("⚠️  Upload skipped (no credentials?)")
    except Exception as e:
        log(f"❌ Upload error: {e}")

# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────
def run_pipeline(topic: str):
    IS_QUICK = "--quick" in sys.argv
    DO_UPLOAD = "--upload" in sys.argv
    SKIP_PORTRAIT_GEN = "--skip-portrait" in sys.argv  # use existing portrait
    SKIP_BG = "--skip-bg" in sys.argv

    log("=" * 60)
    log("🎬 CINEMATIC AVATAR PIPELINE STARTING")
    log(f"   Topic : {topic[:60]}")
    log(f"   Quick : {IS_QUICK}")
    log(f"   Upload: {DO_UPLOAD}")
    log("=" * 60)

    timestamp = int(time.time())
    work_dir  = os.path.join(PROJECT_ROOT, "outputs", f"cine_{timestamp}")
    os.makedirs(work_dir, exist_ok=True)

    script_file  = os.path.join(work_dir, "script.txt")
    audio_file   = os.path.join(work_dir, "voice.wav")
    portrait_file = os.path.join(work_dir, "portrait.png")
    bg_file       = os.path.join(work_dir, "background.mp4")
    face_result   = os.path.join(work_dir, "sadtalker")
    final_video   = os.path.join(work_dir, "final_vertical.mp4")

    # ── 1. SCRIPT ────────────────────────────────────────────────────────────
    log("\n── STEP 1: SCRIPT ──────────────────────────────────────────")
    if IS_QUICK:
        script = FALLBACK_SCRIPT[:80] + "..."
    elif os.path.isfile(topic):
        with open(topic, 'r', encoding='utf-8') as f:
            script = f.read()
        log(f"   Using script from file: {topic}")
    else:
        script = generate_script(topic) or FALLBACK_SCRIPT

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)
    log(f"   Script ({len(script)} chars):\n   {script[:120]}...")

    scene = detect_scene(topic, script)
    log(f"   Detected scene type: {scene.upper()}")

    # ── 2. VOICE ──────────────────────────────────────────────────────────────
    log("\n── STEP 2: VOICE ───────────────────────────────────────────")
    if IS_QUICK and os.path.isfile("inputs/voice.wav"):
        shutil.copy("inputs/voice.wav", audio_file)
        log("   QUICK: reusing existing voice.wav")
    elif not text_to_speech(script, audio_file):
        log("❌ TTS FAILED — aborting")
        return

    # ── 3. PORTRAIT ───────────────────────────────────────────────────────────
    log("\n── STEP 3: PORTRAIT ────────────────────────────────────────")
    existing_portrait = os.path.abspath("inputs/portrait.png")
    if SKIP_PORTRAIT_GEN or IS_QUICK:
        shutil.copy(existing_portrait, portrait_file)
        log(f"   Using existing portrait: {existing_portrait}")
    elif wait_for_comfy(timeout=60):
        log(f"   Generating portrait for scene: {scene}")
        if not generate_portrait_comfy(scene, portrait_file):
            log("   Portrait gen failed — using existing")
            shutil.copy(existing_portrait, portrait_file)
    else:
        log("   ComfyUI offline — using existing portrait")
        shutil.copy(existing_portrait, portrait_file)

    # ── 4. ANIMATED BACKGROUND ────────────────────────────────────────────────
    log("\n── STEP 4: BACKGROUND ──────────────────────────────────────")
    bg_ok = False
    if not SKIP_BG and not IS_QUICK and wait_for_comfy(timeout=30):
        frames = 8 if IS_QUICK else 24
        log(f"   Generating AnimateDiff BG ({frames} frames, scene={scene})")
        bg_ok = generate_background_comfy(scene, bg_file, num_frames=frames)
    if not bg_ok:
        # Fallback: existing stock background
        fallback_bg = os.path.abspath(
            "YouTube_Automation_Free/outputs/AnimateDiff_FuturisticCity_00001.mp4"
        )
        if os.path.isfile(fallback_bg):
            shutil.copy(fallback_bg, bg_file)
            log(f"   Using fallback BG: {fallback_bg}")
            bg_ok = True
        else:
            log("   No BG available — will compose portrait-only")

    # ── 5. SADTALKER ──────────────────────────────────────────────────────────
    log("\n── STEP 5: SADTALKER LIP SYNC ──────────────────────────────")
    face_video = run_sadtalker(audio_file, portrait_file, face_result)
    if not face_video:
        log("❌ SadTalker FAILED — aborting")
        return

    # ── 6. COMPOSE ────────────────────────────────────────────────────────────
    log("\n── STEP 6: COMPOSE 9:16 VERTICAL ───────────────────────────")
    composed = False
    if bg_ok and os.path.isfile(bg_file):
        composed = compose_vertical(face_video, bg_file, audio_file, final_video)
    if not composed:
        compose_portrait_only(face_video, audio_file, final_video)

    if not os.path.isfile(final_video):
        log("❌ COMPOSITING FAILED")
        return

    log("\n" + "=" * 60)
    log(f"🎉 SUCCESS! Final video → {final_video}")
    log("=" * 60)

    # ── 7. UPLOAD ─────────────────────────────────────────────────────────────
    if DO_UPLOAD:
        log("\n── STEP 7: YOUTUBE UPLOAD ──────────────────────────────────")
        title = topic.title()[:100]
        description = (
            f"{script[:400]}\n\n"
            f"#shorts #motivation #ai #viral #youtube"
        )
        publish_at = None
        for i, arg in enumerate(sys.argv):
            if arg == "--publish_at" and i + 1 < len(sys.argv):
                publish_at = sys.argv[i + 1]
        upload_to_youtube(final_video, title, description, publish_at)

    return final_video

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--quick" in sys.argv:
        topic = "AI wealth mindset"
    elif len(sys.argv) < 2:
        print("""Cinematic Avatar Pipeline\n"""
              """Usage: python cinematic_pipeline.py <topic> [--upload] [--publish_at ISO_DATE]\n"""
              """       python cinematic_pipeline.py --quick\n"""
              """Run cinematic_help.py for full documentation.""")
        sys.exit(0)
    else:
        topic = sys.argv[1]

    # Clear old log
    with open(LOG_FILE, "w") as f:
        f.write(f"=== CINEMATIC PIPELINE LOG {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    run_pipeline(topic)
