import os
import shutil

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
