import os
import sys
import subprocess

# Ensure the root directory is in sys.path to find the scripts package
sys.path.append(os.getcwd())

from scripts.comfy_gen import generate_all_assets

PATH_BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
ASSET_IMG = "inputs/style_front.png"
ASSET_BLEND = "work/model/character.blend"
TEMPLATE_BLEND = "YouTube_Automation_Free/assets/character_v2.blend"

def ensure_character(topic="Entrepreneur", character_desc="A charismatic young entrepreneur"):
    """Ensures character.blend and background exist, generating them if necessary."""
    if not os.path.exists(ASSET_IMG) or not os.path.exists("inputs/background.png"):
        print("🎨 Generating character and background assets from AI...")
        # If ComfyUI fails, assets will still be missing, next check handles persistence
        generate_all_assets(topic, character_desc)

    if os.path.exists(ASSET_BLEND):
        print(f"✅ Character Identity Persistent: {ASSET_BLEND}")
        return True

    print("⚡ Character missing. Commencing Layer 1 Staging...")
    
    # 2. Stage in Blender
    # Use a small internal script to create the character.blend
    stage_script = f"""
import bpy
import os

# Check if template exists
if os.path.exists("{os.path.abspath(TEMPLATE_BLEND)}"):
    bpy.ops.wm.open_mainfile(filepath="{os.path.abspath(TEMPLATE_BLEND)}")
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Fallback to plane if template missing
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,1))
    char = bpy.context.object
    char.name = "Character_Mesh"

# Locate character mesh (usually 'Character_Mesh' or based on template)
char_obj = bpy.data.objects.get("Character_Mesh") or bpy.data.objects.get("Mesh") # Adjust as needed

if char_obj:
    # Ensure it has a material
    if not char_obj.data.materials:
        mat = bpy.data.materials.new(name="Character_Mat")
        char_obj.data.materials.append(mat)
    mat = char_obj.data.materials[0]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    # Apply generated texture
    img_path = "{os.path.abspath(ASSET_IMG)}"
    if os.path.exists(img_path):
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(img_path)
        mat.node_tree.links.new(tex.outputs[0], bsdf.inputs["Base Color"])

bpy.ops.wm.save_as_mainfile(filepath="{os.path.abspath(ASSET_BLEND)}")
"""
    
    temp_script = os.path.join(os.getcwd(), "temp_stage.py")
    with open(temp_script, "w") as f: f.write(stage_script)
    
    try:
        subprocess.run([PATH_BLENDER, "-b", "-P", temp_script], check=True)
        print(f"✅ Character staged successfully: {ASSET_BLEND}")
        return True
    except Exception as e:
        print(f"❌ Character Staging Failed: {e}")
        return False
    finally:
        if os.path.exists(temp_script): os.remove(temp_script)

if __name__ == "__main__":
    ensure_character()
