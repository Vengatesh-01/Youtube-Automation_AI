import bpy
import os

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/face_fix_solid.png")
os.makedirs("outputs", exist_ok=True)

def srgb_to_linearrgb(c):
    import math
    if c < 0.04045: return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    import math
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (srgb_to_linearrgb(r/255), srgb_to_linearrgb(g/255), srgb_to_linearrgb(b/255), 1.0)

def fix_face():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mat = bpy.data.materials.get("Skin_Mat")
    if mat:
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        output = nodes.new('ShaderNodeOutputMaterial')
        bsdf.inputs[0].default_value = hex_to_rgb("#F2C29B")
        bsdf.inputs[6].default_value = 0.0
        mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
    
    # Render verify
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE' # Force standard EEVEE for debug
    
    # Camera
    for o in bpy.data.objects:
        if o.type == 'CAMERA': o.location = (0, -0.6, 1.7)
    
    scene.render.filepath = OUTPUT_PATH
    print(f"Rendering solid face to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    bpy.ops.wm.save_as_mainfile(filepath=INPUT_BLEND)

if __name__ == "__main__":
    fix_face()
