import requests
import json
import time
import os
import uuid

COMFY_URL = "http://127.0.0.1:8188/generate"
FIXED_SEED = 42  # For Sasuke/Naruto character consistency

def generate_content(prompt, output_path, type="character"):
    """
    Generates character front/side views or background images.
    """
    # 🎭 FRONT VIEW: Full specification for rigging-ready anime character
    CHAR_BASE = (
        "ninja-style outfit simple for animation optional forehead headband, "
        "sharp expressive eyes with detailed irises and pupils for emotion, "
        "small straight nose, defined jawline, thin lips, calm brooding expression, "
        "medium-length spiky black hair with natural flow, anime Sasuke Uchiha style, "
        "high-resolution PNG ready for Blender UV mapping, "
        "neutral lighting soft shadows minimal cinematic effect, "
        "transparent or pure white background, rigging-ready character design"
    )
    if type == "character_front":
        full_prompt = (
            f"{prompt}, FRONT VIEW portrait, A-pose or T-pose, {CHAR_BASE}, "
            "face symmetrical for blend shape morphs, supports lip-sync phonemes (AI E O U MBP FV), "
            "supports blinking and eye saccade shapes, facial expressions smile frown neutral, "
            "ultra detailed 4K anime illustration"
        )
    elif type == "character_side":
        full_prompt = (
            f"{prompt}, EXACT SIDE VIEW 90-degree profile, {CHAR_BASE}, "
            "shows ear and side hair detail, consistent with front view character, "
            "ultra detailed 4K anime illustration"
        )
    elif type == "background":
        full_prompt = f"{prompt}, cinematic anime background, vibrant colors, wide angle, 9:16 vertical, Naruto/Sasuke universe aesthetic, village or forest scene"
    else:
        full_prompt = prompt

    payload = {
        "prompt": full_prompt,
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "seed": FIXED_SEED
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
