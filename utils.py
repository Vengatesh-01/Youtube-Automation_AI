import os
import shutil
import subprocess

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            # Fallback to ASCII with replacement characters for Windows CMD/PS
            print(str(msg).encode('ascii', 'replace').decode('ascii'))
        except:
            pass

def get_ffmpeg():
    """Resolve ffmpeg binary path — works on both Windows (local) and Linux (Render)."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    
    win_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    if os.path.exists(win_path):
        return win_path
        
    return "ffmpeg"  # Final fallback

def get_audio_duration(file_path):
    ffmpeg_exe = get_ffmpeg()
    
    if os.path.isabs(ffmpeg_exe):
        ffprobe_exe = os.path.join(os.path.dirname(ffmpeg_exe), "ffprobe.exe")
        if not os.path.exists(ffprobe_exe):
            ffprobe_exe = "ffprobe"
    else:
        ffprobe_exe = "ffprobe"
        
    cmd = [ffprobe_exe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception as e:
        safe_print(f"Error getting audio duration: {e}")
    return 0.0
