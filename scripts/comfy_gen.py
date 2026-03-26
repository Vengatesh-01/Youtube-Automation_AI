import requests
import json
import time
import os
import random

COMFY_URL = "http://127.0.0.1:8188"

def generate_content(prompt, output_path, type="generic", negative_prompt=None):
    """
    Generates an image using ComfyUI standard API /prompt.
    """
    with open("debug_flow.log", "a") as f: f.write(f"generate_content called for {type}\n")
    # ... (rest of function remains same, just logging the catch)
    print(f"Generating image with ComfyUI: {prompt[:50]}...")
    
    # Ultra-realistic portrait workflow — 9:16 portrait, 30-step DPM++2M Karras
    REALISTIC_NEGATIVE = (
        negative_prompt or
        "low quality, blurry, cartoon, anime, unrealistic skin, deformed face, bad anatomy, "
        "extra limbs, stiff motion, frozen pose, extreme head movement, side face, occluded face, "
        "flickering, jitter, unstable frames, morphing face, bad lip sync, open mouth freeze, "
        "distorted hands, oversharpen, oversaturated"
    )
    workflow = {
        "1": {
            "inputs": {"ckpt_name": "dreamshaper_8.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {"text": prompt, "clip": ["1", 1]},
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {"text": REALISTIC_NEGATIVE, "clip": ["1", 1]},
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {"width": 512, "height": 896, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {
                "seed": random.randint(0, 10**9),
                "steps": 30,
                "cfg": 7.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "6": {
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
            "class_type": "VAEDecode"
        },
        "7": {
            "inputs": {"images": ["6", 0], "filename_prefix": "CinematicPortrait"},
            "class_type": "SaveImage"
        }
    }

    try:
        # 1. Queue Prompt
        with open("debug_flow.log", "a") as f: f.write(f"Queueing ComfyUI prompt for {type}...\n")
        try:
            response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
            response.raise_for_status() # Ensure we catch HTTP errors
            prompt_id = response.json()['prompt_id']
            print(f"Prompt queued, ID: {prompt_id}")
            with open("debug_flow.log", "a") as f: f.write(f"Prompt queued, ID: {prompt_id}\n")
        except Exception as e:
            print(f"ComfyUI Queue Error: {e}")
            with open("debug_flow.log", "a") as f: f.write(f"FAILED to queue ComfyUI prompt: {e}\n")
            return False

        # 2. Wait for completion
        start_time = time.time()
        while True:
            hist_resp = requests.get(f"{COMFY_URL}/history/{prompt_id}")
            hist_resp.raise_for_status()
            history = hist_resp.json()
            
            if prompt_id in history:
                print("Generation complete!")
                # Extract filename
                outputs = history[prompt_id].get("outputs", {})
                for node_id in outputs:
                    if "images" in outputs[node_id]:
                        filename = outputs[node_id]["images"][0]["filename"]
                        # 3. Download image
                        img_resp = requests.get(f"{COMFY_URL}/view?filename={filename}")
                        img_resp.raise_for_status()
                        
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(img_resp.content)
                        print(f"Image saved to: {output_path}")
                        return True
                        
            if time.time() - start_time > 300: # 5 min timeout
                print("Timed out waiting for ComfyUI.")
                return False
                
            time.sleep(2)
            
    except Exception as e:
        print(f"ComfyUI Generation Error: {e}")
        with open("debug_flow.log", "a") as f: f.write(f"CRITICAL ERROR in generate_content: {e}\n")
        return False

if __name__ == "__main__":
    prompt = (
        f"Subject: highly photorealistic young woman age 25, natural skin texture soft glowing complexion, "
        f"expressive eyes realistic eyelashes well-defined eyebrows, perfectly shaped lips, confident friendly influencer presence, "
        f"subtle smile natural micro-expressions. "
        f"Framing: frontal face centered clearly visible medium close-up upper-body shot, natural posture, no distortion. "
        f"Appearance: modern stylish outfit trendy top jacket clean aesthetic, realistic dark hair soft motion, natural cinematic makeup. "
        f"Environment: soft bokeh background cinematic context-aware. "
        f"Lighting/Camera: professional cinematic lighting soft key light on face, rim light depth separation, "
        f"realistic shadows HDR DSLR-quality rendering face clearly illuminated, stable framing, perfectly aligned for lip sync SadTalker. "
        f"Style: hyper-realistic film-grade 8k quality, vertical 9:16 portrait. not cartoon not anime."
    )
    generate_content(prompt, "inputs/portrait.png")
