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
    if type == "character":
        full_prompt = f"{prompt}, professional character portrait, 3D Pixar style, cinematic lighting, front-facing, neutral expression, white background"
    elif type == "background":
        full_prompt = f"{prompt}, cinematic background, 3D animated style, vibrant colors, matching Pixar character style"
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
    front = generate_content(f"{prompt}, front view", f"{base_path}_front.png", type="character")
    side = generate_content(f"{prompt}, side view", f"{base_path}_side.png", type="character")
    return front, side

if __name__ == "__main__":
    generate_content("A charismatic young entrepreneur", "assets/character.png")
