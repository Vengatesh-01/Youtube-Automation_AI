import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/outputs/model_with_rig.blend")
OUTPUT_PATH = os.path.abspath("outputs/refined_colors_preview.png")
OUTPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend") # Saving back to master
os.makedirs("outputs", exist_ok=True)

def srgb_to_linearrgb(c):
    if c < 0.04045: return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (srgb_to_linearrgb(r/255), srgb_to_linearrgb(g/255), srgb_to_linearrgb(b/255), 1.0)

def setup_refined_materials(mesh_obj):
    # Colors
    colors = {
        "Jacket": "#FF4D4D",
        "Shirt": "#E6E6E6",
        "Pants": "#1A1A1A",
        "Shoes": "#0D0D0D",
        "Hair": "#331A0D",
        "Skin": "#FFC999"
    }
    
    # Clear existing materials
    mesh_obj.data.materials.clear()
    
    # Create Materials
    mats = {}
    for name, hexcode in colors.items():
        mat = bpy.data.materials.new(name=name + "_Mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = hex_to_rgb(hexcode)
            # Adjust roughness/metallic
            if name in ["Jacket", "Shirt", "Pants"]:
                bsdf.inputs[2].default_value = 0.8 # Roughness
            elif name == "Shoes":
                bsdf.inputs[2].default_value = 0.5 # Slightly shinier
            elif name == "Skin":
                bsdf.inputs[2].default_value = 0.6
            elif name == "Hair":
                bsdf.inputs[2].default_value = 0.7
        
        mesh_obj.data.materials.append(mat)
        mats[name] = mat

    # Assign based on detailed height
    h = mesh_obj.dimensions.z
    # Sorting materials into slots for height logic
    # Slots: 0:Jacket, 1:Shirt, 2:Pants, 3:Shoes, 4:Hair, 5:Skin
    
    for poly in mesh_obj.data.polygons:
        avg_z = sum((mesh_obj.matrix_world @ mesh_obj.data.vertices[v].co).z for v in poly.vertices) / len(poly.vertices)
        rel_z = avg_z / h
        
        if rel_z < 0.06: # Shoes
            poly.material_index = list(colors.keys()).index("Shoes")
        elif rel_z < 0.48: # Pants
            poly.material_index = list(colors.keys()).index("Pants")
        elif rel_z < 0.70: # Shirt (Mid/Lower torso)
            poly.material_index = list(colors.keys()).index("Shirt")
        elif rel_z < 0.90: # Jacket (Upper torso/Shoulders/Arms)
            poly.material_index = list(colors.keys()).index("Jacket")
        elif rel_z < 0.96: # Skin (Face)
            poly.material_index = list(colors.keys()).index("Skin")
        else: # Hair (Top of head)
            poly.material_index = list(colors.keys()).index("Hair")

def setup_eevee_next():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except:
        scene.render.engine = 'BLENDER_EEVEE'
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.render_samples = 64
    else:
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 64
        if hasattr(scene.eevee, "use_soft_shadows"):
            scene.eevee.use_soft_shadows = True

def setup_viewport():
    # Only useful for manual opening
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    setup_eevee_next()
    setup_refined_materials(mesh)
    setup_viewport()
    
    # Preview Render
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920
    
    # Light/Camera refresher
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()
    
    # Dramatic Render Set
    bpy.ops.object.light_add(type='POINT', location=(0, -2, 2.5))
    key = bpy.context.object
    key.data.energy = 800
    
    bpy.ops.object.camera_add(location=(0, -4.5, mesh.dimensions.z * 0.6), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.data.lens = 50
    
    print(f"Rendering to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    # Save back to Master
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"Saved master file to {OUTPUT_BLEND}")

if __name__ == "__main__":
    run()
