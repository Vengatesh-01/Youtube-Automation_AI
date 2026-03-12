import os
import subprocess

def test_fusion():
    print("Testing FFmpeg fusion with absolute paths...")
    ffmpeg_path = os.path.abspath(r"venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
    video_input = os.path.abspath(r"videos\pixar_short_221644.mp4")
    audio_input = os.path.abspath(r"voiceovers\voiceover_20260312_222208.mp3")
    output = os.path.abspath(r"fusion_test.mp4")

    if not os.path.exists(video_input):
        print(f"ERROR: Video input missing: {video_input}")
        return
    if not os.path.exists(audio_input):
        print(f"ERROR: Audio input missing: {audio_input}")
        return

    cmd = [
        ffmpeg_path, "-y",
        "-i", video_input,
        "-i", audio_input,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"SUCCESS: Fusion test created: {output}")
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e.stderr}")

if __name__ == "__main__":
    test_fusion()
