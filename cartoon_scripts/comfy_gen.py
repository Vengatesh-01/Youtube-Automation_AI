import requests
import json
import time
import os
import uuid

COMFY_URL = "http://127.0.0.1:8188/generate"

def generate_content(prompt, output_path, type="character"):
    """
    Generates character front/side views or background images.
    """
    if type == "character_front":
        full_prompt = f"{prompt}, front view portrait, t-pose or a-pose, professional character design, 3D Pixar style, cinematic lighting, neutral expression, white background"
    elif type == "character_side":
        full_prompt = f"{prompt}, side view profile, professional character design, 3D Pixar style, cinematic lighting, neutral expression, white background"
    elif type == "background":
        full_prompt = f"{prompt}, cinematic background, 3D animated style, vibrant colors, wide angle, 16:9, matching Pixar style"
    else:
        full_prompt = prompt

    payload = {
        "prompt": full_prompt,
        "width": 1024,
        "height": 1024,
        "steps": 30
    }

    try:
        print(f"🚀 Prompting ComfyUI for {type}: {prompt}")
        resp = requests.post(COMFY_URL, json=payload, timeout=600)
        resp.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
            
        print(f"✅ {type.capitalize()} saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ ComfyUI {type.capitalize()} Gen Failed: {e}")
        return None

def generate_character_set(prompt, base_path):
    """Generates front and side views of the character."""
    front = generate_content(prompt, f"{base_path}_front.png", type="character_front")
    side = generate_content(prompt, f"{base_path}_side.png", type="character_side")
    return front, side

def generate_all_assets(topic, character_desc, inputs_dir="inputs"):
    """One-stop shop for generating character set and matching background."""
    print(f"🎨 Generating all AI assets for: {topic}")
    os.makedirs(inputs_dir, exist_ok=True)
    
    # 1. Background
    bg = generate_content(f"{topic} background", os.path.join(inputs_dir, "background.png"), type="background")
    
    # 2. Character Set
    front, side = generate_character_set(character_desc, os.path.join(inputs_dir, "style"))
    
    return {
        "background": bg,
        "character_front": front,
        "character_side": side
    }

if __name__ == "__main__":
    generate_content("A charismatic young entrepreneur", "assets/character.png")
