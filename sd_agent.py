"""
sd_agent.py — Generates Pixar-style scene images using Pollinations AI (free, no API key)
with HuggingFace Stable Diffusion as fallback.
Each scene uses a character seed for visual consistency within a video.
"""
import os
import time
import requests
import subprocess
import urllib.parse
import random
from utils import safe_print, get_ffmpeg

# Load environment variables from a .env file if present (e.g., HF_TOKEN)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _generate_via_free_api(prompt: str, output_path: str, seed: int = None) -> str:
    """Primary: Use Lexica.art (highly reliable free AI image search)."""
    img_path = output_path.replace(".mp4", ".png")
    
    # Clean the prompt by removing the character seed/long details which Lexica might not match well
    # Just grab the core visual elements
    core_prompt = prompt.split(',')[0:3]
    clean_prompt = ",".join(core_prompt).strip()
    encoded_prompt = urllib.parse.quote(clean_prompt)
    
    url_lexica = f"https://lexica.art/api/v1/search?q={encoded_prompt}"
    safe_print(f"[SD] Lexica API request (prompt: {clean_prompt})...")
    
    for attempt in range(2):
        try:
            response = requests.get(url_lexica, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "images" in data and len(data["images"]) > 0:
                    # Pick a random image from the top 5 results for variety
                    idx = random.randint(0, min(4, len(data["images"]) - 1))
                    img_url = data["images"][idx]["src"]
                    
                    img_res = requests.get(img_url, timeout=30)
                    if img_res.status_code == 200 and len(img_res.content) > 5000:
                        with open(img_path, "wb") as f:
                            f.write(img_res.content)
                        safe_print(f"[SD] Lexica API success: {img_path}")
                        return img_path
            safe_print(f"[SD] Lexica attempt {attempt+1} failed or returned no images.")
        except Exception as e:
            safe_print(f"[SD] Lexica attempt {attempt+1} error: {e}")
        time.sleep(2)
        
    return None


def _generate_via_huggingface(prompt: str, output_path: str, seed: int = None) -> str:
    """Fallback: Use HuggingFace Stable Diffusion XL API."""
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        safe_print("[SD] HF_TOKEN not found. Skipping HuggingFace fallback.")
        return None

    img_path = output_path.replace(".mp4", ".png")
    
    local_sd_url = os.getenv("LOCAL_SD_URL")
    if local_sd_url:
        API_URL = local_sd_url
        safe_print("[SD] Using local Stable Diffusion endpoint from LOCAL_SD_URL.")
    else:
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

    headers = {"Authorization": f"Bearer {hf_token}"}
    
    payload = {
        "inputs": prompt + ", vertical, 9:16 aspect ratio, high quality, highly detailed",
        "parameters": {}
    }
    if seed:
        payload["parameters"]["seed"] = seed

    for attempt in range(2):
        try:
            safe_print(f"[SD] HuggingFace attempt {attempt+1}...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200 and len(response.content) > 5000:
                with open(img_path, "wb") as f:
                    f.write(response.content)
                safe_print(f"[SD] HuggingFace success: {img_path}")
                return img_path
            else:
                safe_print(f"[SD] HuggingFace attempt {attempt+1} failed: HTTP {response.status_code}")
                try:
                    error_msg = response.json()
                    safe_print(f"     Reason: {error_msg}")
                except:
                    pass
        except Exception as e:
            safe_print(f"[SD] HuggingFace attempt {attempt+1} error: {e}")
        
        if attempt < 1:
            time.sleep(5)

    return None


def _fallback_image(output_path: str):
    """Last resort: download a stock image."""
    fallback_url = "https://loremflickr.com/1080/1920/animation,3d"
    try:
        response = requests.get(fallback_url, timeout=30)
        if response.status_code == 200:
            img_path = output_path.replace(".mp4", ".png")
            with open(img_path, "wb") as f:
                f.write(response.content)
            safe_print(f"[SD] Fallback stock image downloaded: {img_path}")
            return img_path
    except Exception as e:
        safe_print(f"[SD] Fallback also failed: {e}")
    safe_print("[SD] All image generation attempts failed. Will use black frame.")
    return None


def generate_scene_image(prompt: str, output_path: str, seed: int = None) -> str:
    """
    Generate an image for a scene. Tries in order:
    1. Pollinations AI (free, reliable, no key needed)
    2. HuggingFace Stable Diffusion XL (requires HF_TOKEN)
    3. Stock photo fallback
    """
    safe_print(f"[SD] Generating scene image (seed={seed})...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Primary: Free Alternative APIs (Airforce / Hercai)
    result = _generate_via_free_api(prompt, output_path, seed=seed)
    if result:
        return result

    # Fallback 1: HuggingFace
    result = _generate_via_huggingface(prompt, output_path, seed=seed)
    if result:
        return result

    # Fallback 2: Stock photo
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
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
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
            stderr_text = res.stderr.decode('utf-8', errors='replace')[-300:] if res.stderr else "No stderr"
            safe_print(f"[SD] FFmpeg error: {stderr_text}")
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
