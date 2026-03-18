import os
import sys
import subprocess

# Ensure the root directory is in sys.path to find the scripts package
sys.path.append(os.getcwd())

from cartoon_scripts.comfy_gen import generate_character_image

PATH_BLENDER = os.environ.get("BLENDER_PATH", r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
ASSET_IMG = "inputs/style_front.png"
ASSET_BLEND = "work/model/character.blend"
TEMPLATE_BLEND = "assets/character_v2.blend"

def ensure_character():
    """Ensures character.blend exists, generating it if necessary."""
    if os.path.exists(ASSET_BLEND):
        print(f"✅ Character Identity Persistent: {ASSET_BLEND}")
        return True

    print("⚡ Character missing. Commencing Layer 1 Generation...")
    
    # 1. Generate Image if missing
    if not os.path.exists(ASSET_IMG):
        prompt = "A friendly AI mascot character, soft 3D style" # Generic fallback
        if not generate_character_image(prompt, ASSET_IMG):
            # If ComfyUI fails, we use a placeholder or error
            print("⚠️ ComfyUI Failed. Using internal proxy fallback...")
    
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
    
    temp_script = "temp_stage.py"
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
