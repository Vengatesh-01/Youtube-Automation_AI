import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/orange_jacket_preview.png")
OUTPUT_BLEND = INPUT_BLEND # Update master
os.makedirs("outputs", exist_ok=True)

def srgb_to_linearrgb(c):
    if c < 0.04045: return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (srgb_to_linearrgb(r/255), srgb_to_linearrgb(g/255), srgb_to_linearrgb(b/255), 1.0)

def setup_scene():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.eevee.render_samples = 64
        scene.eevee.preview_samples = 16
    except:
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.taa_render_samples = 64
        if hasattr(scene.eevee, "use_soft_shadows"):
            scene.eevee.use_soft_shadows = True

def assign_v3_materials(mesh_obj):
    # Requirements
    colors = {
        "Jacket": "#F28C28", # Solid Orange
        "Shirt": "#E6E6E6",  # Light Gray/White
        "Pants": "#1A1A1A",  # Dark Charcoal
        "Shoes": "#0D0D0D",  # Near Black
        "Hair": "#5A341C",   # Brown
        "Skin": "#F2C29B"    # Light Natural
    }
    
    mesh_obj.data.materials.clear()
    mats_list = list(colors.keys())
    idx_map = {name: i for i, name in enumerate(mats_list)}
    
    for name in mats_list:
        mat = bpy.data.materials.new(name=name + "_Mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = hex_to_rgb(colors[name])
            bsdf.inputs[6].default_value = 0.0 # Metallic (Fabric focus)
            bsdf.inputs[2].default_value = 0.9 # Roughness (Matte fabric)
            if name == "Skin":
                bsdf.inputs[2].default_value = 0.6 # Softer skin
        mesh_obj.data.materials.append(mat)

    vgroups = {g.index: g.name for g in mesh_obj.vertex_groups}
    h = mesh_obj.dimensions.z
    
    for poly in mesh_obj.data.polygons:
        group_counts = {}
        poly_z = 0
        for v_idx in poly.vertices:
            v_obj = mesh_obj.data.vertices[v_idx]
            poly_z += (mesh_obj.matrix_world @ v_obj.co).z
            for g in v_obj.groups:
                g_name = vgroups.get(g.group, "")
                if g_name:
                    group_counts[g_name] = group_counts.get(g_name, 0.0) + g.weight
        
        avg_z = poly_z / len(poly.vertices)
        rel_z = avg_z / h
        
        dominant_group = "None"
        if group_counts:
            max_w = -1.0
            for gn, w in group_counts.items():
                if w > max_w:
                    max_w = w
                    dominant_group = gn
        
        # Mapping Logic v3
        mat_key = "Shirt" # Default background
        
        if "Head" in dominant_group or "Neck" in dominant_group:
            if rel_z > 0.94:
                mat_key = "Hair"
            else:
                mat_key = "Skin"
        elif "Arm" in dominant_group:
            # Check for hands (lowest part of arm groups if A-pose)
            if "Lower" in dominant_group and rel_z < 0.6: 
                mat_key = "Skin"
            else:
                mat_key = "Jacket"
        elif "Shoulder" in dominant_group:
            mat_key = "Jacket"
        elif "Spine" in dominant_group:
            # Segment Torso into Jacket (top/outer) and Shirt (mid)
            if rel_z > 0.72:
                mat_key = "Jacket"
            else:
                mat_key = "Shirt"
        elif "Hips" in dominant_group or "Leg" in dominant_group:
            if rel_z < 0.08:
                mat_key = "Shoes"
            else:
                mat_key = "Pants"
        
        poly.material_index = idx_map.get(mat_key, 0)

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    setup_scene()
    assign_v3_materials(mesh)
    
    # Lighting Refined for Orange pop
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()
    
    # User's requested locations or similar
    bpy.ops.object.light_add(type='POINT', location=(0, -3, 2))
    key = bpy.context.object
    key.data.energy = 1200
    
    bpy.ops.object.camera_add(location=(0, -4, mesh.dimensions.z * 0.6), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080 # Square body shot
    
    bpy.context.scene.render.filepath = OUTPUT_PATH
    print(f"Rendering to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"Master file updated: {OUTPUT_BLEND}")

if __name__ == "__main__":
    run()
