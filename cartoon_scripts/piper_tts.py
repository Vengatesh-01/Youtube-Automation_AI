import subprocess
import os
import shutil
import asyncio

def text_to_speech(text, output_file="outputs/audio.wav", model_path="assets/piper_model.onnx"):
    """
    Converts text to speech.
    Primary: Piper TTS
    Fallback 1: edge-tts (Microsoft Edge TTS)
    Fallback 2: pyttsx3
    """
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # Dramatic pacing for viral content
    refined = text.replace("...", ", , , ").replace(".", ". ").replace("?", "? ").replace("!", "! ")

    # --- PRIMARY: Piper TTS ---
    PIPER_EXE = os.environ.get("PIPER_PATH", r"C:\Users\User\Downloads\piper_extracted\piper.exe")
    if not os.path.exists(PIPER_EXE):
        PIPER_EXE = shutil.which("piper") or ""

    if PIPER_EXE and os.path.exists(PIPER_EXE if os.sep in PIPER_EXE else PIPER_EXE):
        try:
            proc = subprocess.Popen(
                [PIPER_EXE, "--model", model_path, "--output_file", output_file],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, stderr = proc.communicate(input=refined)
            if proc.returncode == 0:
                print(f"🎙️ Piper audio: {output_file}")
                return True
            print(f"⚠️ Piper error: {stderr[:200]}")
        except Exception as e:
            print(f"⚠️ Piper failed: {e}")

    # --- FALLBACK 1: edge-tts ---
    try:
        import edge_tts
        print("🔄 Falling back to edge-tts...")
        mp3_file = output_file.replace(".wav", ".mp3")

        async def _speak():
            communicate = edge_tts.Communicate(refined, voice="en-US-GuyNeural", rate="+10%")
            await communicate.save(mp3_file)

        asyncio.run(_speak())

        # Convert mp3 -> wav using ffmpeg
        if shutil.which("ffmpeg"):
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_file, "-ar", "22050", "-ac", "1", output_file],
                check=True, capture_output=True
            )
            os.remove(mp3_file)
        else:
            os.rename(mp3_file, output_file)

        print(f"✅ edge-tts audio: {output_file}")
        return True
    except Exception as e:
        print(f"⚠️ edge-tts failed: {e}")

    # --- FALLBACK 2: pyttsx3 (offline) ---
    try:
        import pyttsx3
        print("🔄 Falling back to pyttsx3...")
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.save_to_file(refined, output_file)
        engine.runAndWait()
        print(f"✅ pyttsx3 audio: {output_file}")
        return True
    except Exception as e:
        print(f"❌ All TTS methods failed: {e}")
        return False

if __name__ == "__main__":
    text_to_speech("This is Sasuke. The power of the Sharingan is beyond comprehension.")
