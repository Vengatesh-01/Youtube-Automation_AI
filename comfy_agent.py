import requests
import json
import time
import os
import uuid
from utils import safe_print

COMFY_URL = "http://127.0.0.1:8188"

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req =  requests.post(f"{COMFY_URL}/prompt", data=data)
    return req.json()

def check_status(prompt_id):
    req = requests.get(f"{COMFY_URL}/history/{prompt_id}")
    return req.json()

def generate_local_animation(prompt_text, output_filename, model_name="ltx-video-2b-v0.9.safetensors"):
    """
    Generates a short video segment using local ComfyUI nodes:
    - LTXVideo for core video generation
    - WanAnimate-Enhancer for character expressions/motion
    - WAS Node Suite for filters and style
    - VideoHelperSuite for MP4/H264 recording
    """
    workflow = {
        "10": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "LTXVideoCheckpointLoader"
        },
        "11": {
            "inputs": {
                "text": prompt_text + ", 3D Pixar style, cinematic lighting, vertical 9:16",
                "clip": ["10", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "12": {
            "inputs": {
                "model": ["10", 0],
                "positive": ["11", 0],
                "negative": ["13", 0],
                "latent_image": ["14", 0],
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            },
            "class_type": "LTXVideoSampler"
        },
        "13": {
            "inputs": {
                "text": "low quality, text, watermark, distorted, blurry",
                "clip": ["10", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "14": {
            "inputs": {
                "width": 1080,
                "height": 1920,
                "length": 16, 
                "batch_size": 1
            },
            "class_type": "LTXVideoEmptyLatent"
        },
        "15": {
            "inputs": {
                "samples": ["12", 0],
                "vae": ["10", 2]
            },
            "class_type": "LTXVideoVAEDecode"
        },
        "20": {
            "inputs": {
                "images": ["15", 0],
                "motion_scale": 1.0,
                "expression_type": "happy",
                "face_enhance": True
            },
            "class_type": "WanAnimateEnhancer"
        },
        "30": {
            "inputs": {
                "images": ["20", 0],
                "brightness": 0.05,
                "contrast": 1.1,
                "saturation": 1.2
            },
            "class_type": "WAS_Image_Adjustment"
        },
        "40": {
            "inputs": {
                "images": ["30", 0],
                "filenames": "ShortSegment_" + str(uuid.uuid4())[:8],
                "fps": 24,
                "format": "video/h264-mp4"
            },
            "class_type": "VHS_VideoCombine"
        }
    }

    try:
        response = queue_prompt(workflow)
        prompt_id = response['prompt_id']
        safe_print(f"[ComfyUI] Queued local video generation {prompt_id}...")

        while True:
            history = check_status(prompt_id)
            if prompt_id in history:
                output = history[prompt_id]['outputs']['40']['gifs'][0]
                filename = output['filename']
                
                # Fetch final MP4 link
                video_url = f"{COMFY_URL}/view?filename={filename}&type=output"
                video_data = requests.get(video_url).content
                
                os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                with open(output_filename, "wb") as f:
                    f.write(video_data)
                
                safe_print(f"✅ [ComfyUI] Local video saved: {output_filename}")
                return output_filename
            
            time.sleep(3)
    except Exception as e:
        safe_print(f"❌ [ComfyUI] Error: {e}")
        return None

if __name__ == "__main__":
    # Test generation
    generate_key_frame("A futuristic city at sunset, Pixar style, highly detailed", "outputs/test_comfy.png")
