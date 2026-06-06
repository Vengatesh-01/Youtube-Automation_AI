"""
sd_agent.py — Generates Pixar-style scene images using Pollinations AI (free, no API key).
Each scene uses a character seed for visual consistency within a video.
"""
import os
import time
import requests
import subprocess
import urllib.parse
from utils import safe_print, get_ffmpeg


def _fallback_image(output_path: str):
    fallback_url = "https://loremflickr.com/1080/1920/animation,3d"
    try:
        response = requests.get(fallback_url, timeout=30)
        if response.status_code == 200:
            img_path = output_path.replace(".mp4", ".png")
            with open(img_path, "wb") as f:
                f.write(response.content)
            safe_print(f"[SD] Fallback image downloaded: {img_path}")
            return img_path
    except Exception as e:
        safe_print(f"[SD] Fallback also failed: {e}")
    safe_print("[SD] All attempts failed. Using fallback black frame.")
    return None

def generate_scene_image(prompt: str, output_path: str, seed: int = None) -> bool:
    """
    Generate an image using Stable Diffusion (via Hugging Face Inference API).
    Falls back to a stock photo if the API fails or token is missing.
    """
    safe_print(f"[SD] Generating scene image (seed={seed}) via Stable Diffusion...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        safe_print("⚠️ [SD] HF_TOKEN not found in environment (.env).")
        safe_print("[SD] Stable Diffusion requires a free Hugging Face token. Falling back to placeholder...")
        return _fallback_image(output_path)

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    # SDXL works best when prompted for aspect ratio textually in the free API
    payload = {
        "inputs": prompt + ", vertical, 9:16 aspect ratio, high quality, highly detailed",
    }

    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                img_path = output_path.replace(".mp4", ".png")
                with open(img_path, "wb") as f:
                    f.write(response.content)
                safe_print(f"[SD] Image downloaded successfully: {img_path}")
                return img_path
            else:
                safe_print(f"[SD] Attempt {attempt+1} failed: HTTP {response.status_code}")
                # Print error reason if available (helps with 'Model is loading' errors)
                try:
                    error_msg = response.json()
                    safe_print(f"     Reason: {error_msg}")
                except:
                    pass
                time.sleep(15)
        except Exception as e:
            safe_print(f"[SD] Attempt {attempt+1} error: {e}")
            time.sleep(15)

    safe_print("[SD] Stable Diffusion failed. Falling back to free placeholder image...")
    return _fallback_image(output_path)


def image_to_video(image_path: str, output_path: str, duration: int = 6, effect: str = "zoom_in") -> bool:
    """
    Convert a still image to a video with Ken Burns motion effect using FFmpeg.
    Effects: zoom_in, zoom_out, pan_left, pan_right
    """
    fps = 30
    frames = fps * duration

    if effect == "zoom_in":
        zoom = f"'min(1.0+0.0020*on,1.5)'"
        x = "'iw/2-(iw/zoom/2)'"
        y = "'ih/2-(ih/zoom/2)'"
    elif effect == "zoom_out":
        zoom = f"'max(1.5-0.0020*on,1.0)'"
        x = "'iw/2-(iw/zoom/2)'"
        y = "'ih/2-(ih/zoom/2)'"
    elif effect == "pan_left":
        zoom = "'1.3'"
        x = f"'(iw-iw/zoom)*on/{frames}'"
        y = "'ih/2-(ih/zoom/2)'"
    else:  # pan_right
        zoom = "'1.3'"
        x = f"'(iw-iw/zoom)*(1-on/{frames})'"
        y = "'ih/2-(ih/zoom/2)'"

    # Scale input up first so zoompan has pixels to work with
    vf = (
        f"scale=2160:3840,"
        f"zoompan=z={zoom}:x={x}:y={y}:d={frames}:s=1080x1920:fps={fps},"
        f"scale=1080:1920"
    )

    ffmpeg_exe = get_ffmpeg()
    # Fallback: generate black frame if no image
    if image_path is None:
        cmd = [
            ffmpeg_exe, "-y", "-nostdin",
            "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y", "-nostdin",
            "-loop", "1", "-i", image_path,
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path
        ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        if res.returncode == 0 and os.path.exists(output_path):
            safe_print(f"[SD] Video segment ready ({effect}): {output_path}")
            # Cleanup source image
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception:
                    pass
            return True
        else:
            safe_print(f"[SD] FFmpeg error: {res.stderr[-300:]}")
            return False
    except Exception as e:
        safe_print(f"[SD] FFmpeg exception: {e}")
        return False


def generate_local_animation(prompt: str, output_path: str, seed: int = None, effect: str = "zoom_in") -> bool:
    """
    Main entry point: generate image then convert to animated video segment.
    """
    img_path = generate_scene_image(prompt, output_path, seed=seed)
    return image_to_video(img_path, output_path, duration=6, effect=effect)
