"""
sd_agent.py — Generates Pixar-style scene images using Pollinations AI (free, no API key).
Each scene uses a character seed for visual consistency within a video.
"""
import os
import time
import requests
import subprocess
import urllib.parse
from utils import safe_print


def generate_scene_image(prompt: str, output_path: str, seed: int = None) -> bool:
    """
    Generate a 1080x1920 vertical image from Pollinations AI using Flux model.
    Falls back to a black frame if the API fails.
    """
    safe_print(f"[SD] Generating scene image (seed={seed})...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    encoded = urllib.parse.quote(prompt)
    seed_param = f"&seed={seed}" if seed is not None else ""
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1920&model=flux&nologo=true{seed_param}"
    )

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200 and len(response.content) > 5000:
                img_path = output_path.replace(".mp4", ".png")
                with open(img_path, "wb") as f:
                    f.write(response.content)
                safe_print(f"[SD] Image downloaded: {img_path}")
                return img_path
            else:
                safe_print(f"[SD] Attempt {attempt+1} failed: HTTP {response.status_code}")
                time.sleep(5)
        except Exception as e:
            safe_print(f"[SD] Attempt {attempt+1} error: {e}")
            time.sleep(5)

    safe_print("[SD] All attempts failed. Using fallback black frame.")
    return None


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

    # Fallback: generate black frame if no image
    if image_path is None:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30",
            "-t", str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path
        ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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
