import os
import sys
import shutil
import subprocess

ASSET_BLEND = "work/model/character.blend"
TEMPLATE_BLEND = os.path.abspath("assets/character_v2.blend")
PATH_BLENDER = os.environ.get("BLENDER_PATH", r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
if not os.path.exists(PATH_BLENDER):
    PATH_BLENDER = shutil.which("blender") or PATH_BLENDER

def ensure_character(topic="Anime Character", character_desc="Sasuke Uchiha style anime character"):
    """Ensures character.blend exists. Copies character_v2.blend template as fallback."""
    os.makedirs("work/model", exist_ok=True)
    
    # Fast-path: already staged
    if os.path.exists(ASSET_BLEND):
        print(f"✅ Character Identity Persistent: {ASSET_BLEND}")
        return True

    print("⚡ Character missing — using template fallback...")
    
    # Try ComfyUI generation (best-effort, non-blocking)
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cartoon_scripts.comfy_gen import generate_all_assets
        generate_all_assets(topic, character_desc)
    except Exception as e:
        print(f"⚠️ ComfyUI generation skipped: {e}")

    if os.path.exists(ASSET_BLEND):
        return True

    # FALLBACK: Copy character_v2.blend as character.blend
    if os.path.exists(TEMPLATE_BLEND):
        print(f"📋 Copying template: {TEMPLATE_BLEND} -> {ASSET_BLEND}")
        shutil.copy(TEMPLATE_BLEND, ASSET_BLEND)
        print(f"✅ Character staged from template.")
        return True

    print("❌ No character template found at:", TEMPLATE_BLEND)
    return False

if __name__ == "__main__":
    ensure_character()
