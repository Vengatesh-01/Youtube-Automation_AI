"""
generate_guilt_short.py
=======================
End-to-end pipeline to generate a 15-30s YouTube Shorts video on "Overcoming Guilt".

Steps:
  1. Generate script via Ollama (with offline fallback) → scripts/overcoming_guilt.txt
  2. Generate voice via pyttsx3                         → voiceovers/guilt_voice.wav
  3. Render Blender 3D animation with lip-sync          → outputs/shorts.mp4
"""

import os
import sys
import subprocess
import time

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SCRIPT_TXT = os.path.join(BASE_DIR, "scripts", "overcoming_guilt.txt")
VOICE_WAV  = os.path.join(BASE_DIR, "voiceovers", "guilt_voice.wav")
OUTPUT_MP4 = os.path.join(BASE_DIR, "outputs", "shorts.mp4")
CHAR_BLEND = os.path.join(BASE_DIR, "assets", "character.blend")
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
SHORTS_GEN  = os.path.join(BASE_DIR, "guilt_blender_scene.py")

os.makedirs(os.path.join(BASE_DIR, "scripts"),    exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "voiceovers"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "outputs"),    exist_ok=True)

GUILT_SCRIPT = """\
Feeling guilty? You are not alone.
We all carry mistakes we wish we could undo.
But guilt is not meant to imprison you.
Have you ever thought that forgiving yourself is the bravest thing you can do?
Every single person you admire has messed up too.
The difference is they chose to learn, not to suffer.
What would your life look like if you let go today?
You are more than your worst moment.
Let go, forgive yourself, and move forward.\
"""

# ─────────────────────────────────────────────
# STEP 1 — Script
# ─────────────────────────────────────────────
def step1_script():
    print("\n━━━ STEP 1: Script ━━━")
    # Try Ollama first
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": (
                    "Write a 15-25 second motivational YouTube Shorts script about 'Overcoming Guilt'.\n"
                    "Rules:\n"
                    "- Start with hook: 'Feeling guilty? You are not alone.'\n"
                    "- 8-10 short punchy sentences, one per line\n"
                    "- 1-2 rhetorical questions to engage viewers\n"
                    "- End with: 'Let go, forgive yourself, and move forward.'\n"
                    "- Plain text only, one sentence per line, no scene headings, no brackets\n"
                    "- Total ~80-100 words"
                ),
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        if raw and len(raw) > 50:
            # Clean up any markdown/meta text
            import re
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            lines = [l for l in lines if not l.startswith('#') and not l.startswith('**')]
            script_text = "\n".join(lines)
            with open(SCRIPT_TXT, "w", encoding="utf-8") as f:
                f.write(script_text)
            print(f"✅ Ollama script saved → {SCRIPT_TXT}")
            return SCRIPT_TXT
    except Exception as e:
        print(f"⚠️  Ollama unavailable ({e}). Using built-in fallback script.")

    # Fallback: use hardcoded script
    with open(SCRIPT_TXT, "w", encoding="utf-8") as f:
        f.write(GUILT_SCRIPT)
    print(f"✅ Fallback script saved → {SCRIPT_TXT}")
    return SCRIPT_TXT


# ─────────────────────────────────────────────
# STEP 2 — Voice
# ─────────────────────────────────────────────
def step2_voice(script_path):
    print("\n━━━ STEP 2: Voice (pyttsx3) ━━━")
    try:
        import pyttsx3, re

        with open(script_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Strip emotion cues like [thoughtful]
        speech_text = re.sub(r'\[.*?\]', '', raw).strip()

        engine = pyttsx3.init()

        # Voice selection: prefer natural-sounding voices
        voices = engine.getProperty('voices')
        chosen = None
        for v in voices:
            name = v.name.lower()
            if any(k in name for k in ("david", "zira", "andrew", "mark", "aria")):
                chosen = v
                break
        if chosen:
            engine.setProperty('voice', chosen.id)
            print(f"   Voice: {chosen.name}")

        # Slightly slower, natural pace
        engine.setProperty('rate', 155)
        engine.setProperty('volume', 0.95)

        engine.save_to_file(speech_text, VOICE_WAV)
        engine.runAndWait()

        if os.path.exists(VOICE_WAV) and os.path.getsize(VOICE_WAV) > 0:
            print(f"✅ Voice saved → {VOICE_WAV}")
            return VOICE_WAV
        else:
            print("❌ Voice file empty or missing.")
            return None
    except Exception as e:
        print(f"❌ pyttsx3 error: {e}")
        return None


# ─────────────────────────────────────────────
# STEP 3 — Blender Render
# ─────────────────────────────────────────────
def step3_blender(voice_path, script_path):
    print("\n━━━ STEP 3: Blender Render ━━━")

    if not os.path.exists(BLENDER_EXE):
        print(f"❌ Blender not found: {BLENDER_EXE}")
        return False

    if not os.path.exists(CHAR_BLEND):
        print("⚠️  character.blend missing. Attempting to generate it first...")
        gen_script = os.path.join(BASE_DIR, "generate_character_asset.py")
        if os.path.exists(gen_script):
            result = subprocess.run(
                [BLENDER_EXE, "-b", "--python", gen_script],
                capture_output=True, text=True
            )
            if not os.path.exists(CHAR_BLEND):
                print("❌ Failed to create character.blend")
                print(result.stderr[-1000:])
                return False
        else:
            print("❌ generate_character_asset.py not found either.")
            return False

    # Read script lines (strip emotion cues)
    import re
    with open(script_path, "r", encoding="utf-8") as f:
        lines = [re.sub(r'\[.*?\]', '', l).strip() for l in f.readlines()]
    sentences = [l for l in lines if l]
    captions_json = __import__('json').dumps(sentences)

    voice_abs  = os.path.abspath(voice_path) if voice_path else ""
    output_abs = os.path.abspath(OUTPUT_MP4)

    env = os.environ.copy()
    env["SHORTS_AUDIO"]    = voice_abs
    env["SHORTS_TOPIC"]    = "Overcoming Guilt"
    env["SHORTS_OUTPUT"]   = output_abs
    env["SHORTS_CAPTIONS"] = captions_json
    env["TOTAL_SEC"]       = "25"

    blender_script = os.path.join(BASE_DIR, "guilt_blender_scene.py")

    cmd = [
        BLENDER_EXE, "-b", CHAR_BLEND,
        "-P", blender_script
    ]

    print(f"   Running: {' '.join(cmd)}")
    print(f"   Output:  {output_abs}")
    print("   (This may take 3-10 minutes on CPU...)")

    result = subprocess.run(cmd, env=env, capture_output=False, text=True)

    log_path = os.path.join(BASE_DIR, "blender_guilt.log")
    with open(log_path, "w", encoding="utf-8") as lf:
        lf.write("Return code: " + str(result.returncode) + "\n")

    if os.path.exists(output_abs) and os.path.getsize(output_abs) > 10000:
        print(f"\n✅ Video rendered → {output_abs}")
        size_mb = os.path.getsize(output_abs) / (1024 * 1024)
        print(f"   Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Render failed or output too small. Check blender_guilt.log")
        return False


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🎬 YouTube Shorts: 'Overcoming Guilt'")
    print("=" * 55)

    script_path = step1_script()
    if not script_path:
        print("❌ Script generation failed. Aborting.")
        sys.exit(1)

    voice_path = step2_voice(script_path)
    # Voice is optional — Blender can still render without audio

    ok = step3_blender(voice_path, script_path)

    if ok:
        print("\n🎉 Pipeline complete!")
        print(f"   Output: {OUTPUT_MP4}")
    else:
        print("\n❌ Pipeline finished with errors.")
        sys.exit(1)
