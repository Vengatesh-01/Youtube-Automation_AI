import os
import time
import requests
import subprocess
from utils import safe_print

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def generate_local_animation(prompt_text, output_filename, model_name=None):
    """
    Hooks into the Hugging Face Inference API to generate a Stable Diffusion image,
    and then constructs a 5-second MP4 loop using FFmpeg.
    """
    safe_print(f"[SD_AGENT] Sending prompt to Hugging Face API: {prompt_text[:50]}...")

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        safe_print("⚠️ [SD_AGENT] HF_TOKEN is not set. Falling back to dummy generator.")
        success = False
    else:
        # Use SDXL or a high-quality model endpoint on HF
        hf_api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        payload = {
            "inputs": prompt_text,
            "parameters": {
                "num_inference_steps": 25,
                "guidance_scale": 7.0
            }
        }

        image_path = f"outputs/temp_sd_{int(time.time())}.png"
        success = False

        try:
            # Add delay to avoid aggressive rate limiting
            time.sleep(2)
            response = requests.post(hf_api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                safe_print("[SD_AGENT] Successfully gathered frame from Hugging Face API.")
                success = True
            elif response.status_code == 503:
                # Model is loading
                safe_print("[SD_AGENT] Model is loading... retrying in 15 seconds.")
                time.sleep(15)
                response = requests.post(hf_api_url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    success = True
                    safe_print("[SD_AGENT] Successfully gathered frame on retry.")
                else:
                    safe_print(f"⚠️ [SD_AGENT] API error on retry {response.status_code}: {response.text}")
            else:
                safe_print(f"⚠️ [SD_AGENT] API returned error {response.status_code}. Response: {response.text}")
        except Exception as e:
            safe_print(f"⚠️ [SD_AGENT] Error connecting to HF API: {e}")

    # Fallback to an empty/black frame generation via FFmpeg if REST failed
    if not success:
        safe_print("⚠️ [SD_AGENT] Using fallback auto-generation (black screen overlay) due to missing API/Token.")
    
    safe_print("[SD_AGENT] Converting structural image slice to 5-second motion video...")
    os.makedirs(os.path.dirname(os.path.abspath(output_filename)), exist_ok=True)
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path if success else "assets/fallback_bg.png",
        "-t", "5",
        "-filter_complex", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=150",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_filename
    ]

    try:
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        safe_print(f"✅ [SD_AGENT] Rendered 5s segment successfully: {output_filename}")
        
        # Cleanup
        if success and os.path.exists(image_path):
            os.remove(image_path)
            
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"❌ [SD_AGENT] FFmpeg generation failed: {e}")
        return False
