import os
from moviepy import ColorClip

def test_no_audio():
    print("[TEST] MoviePy Writing (NO AUDIO) Test...")
    clip = ColorClip(size=(1080, 1920), color=(20, 20, 30), duration=2)
    
    # Force FFmpeg path
    FFMPEG_PATH = r"c:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
    os.environ["MOVIEPY_FFMPEG_BINARY"] = FFMPEG_PATH
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

    print("[TEST] Writing file (no audio)...")
    try:
        clip.write_videofile("test_no_audio.mp4", fps=24, logger="bar", audio=False)
        print("[TEST] Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_no_audio()
