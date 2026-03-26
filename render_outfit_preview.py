import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/outputs/model_with_rig.blend")
OUTPUT_PATH = os.path.abspath("outputs/outfit_preview.png")
os.makedirs("outputs", exist_ok=True)

def setup_materials(mesh_obj):
    # Create Materials
    def create_mat(name, color):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = color
        return mat

    top_mat = create_mat("Top_Mat", (0.8, 0.75, 0.7, 1.0)) # Beige/Light Gray
    pants_mat = create_mat("Pants_Mat", (0.05, 0.05, 0.05, 1.0)) # Dark Gray/Black
    shoes_mat = create_mat("Shoes_Mat", (0.9, 0.9, 0.9, 1.0)) # White
    skin_mat = create_mat("Skin_Mat", (0.9, 0.7, 0.6, 1.0)) # Stylized Skin
    
    mesh_obj.data.materials.append(top_mat)   # Slot 0
    mesh_obj.data.materials.append(pants_mat) # Slot 1
    mesh_obj.data.materials.append(shoes_mat) # Slot 2
    mesh_obj.data.materials.append(skin_mat)  # Slot 3
    
    # Assign based on height
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    h = mesh_obj.dimensions.z
    # We iterate over polygons and assign material index
    for poly in mesh_obj.data.polygons:
        # Get average Z of polygon vertices
        avg_z = 0
        for vert_idx in poly.vertices:
            avg_z += (mesh_obj.matrix_world @ mesh_obj.data.vertices[vert_idx].co).z
        avg_z /= len(poly.vertices)
        
        rel_z = avg_z / h
        
        if rel_z < 0.1: # Shoes
            poly.material_index = 2
        elif rel_z < 0.5: # Pants
            poly.material_index = 1
        elif rel_z < 0.85: # Top
            poly.material_index = 0
        else: # Face/Head
            poly.material_index = 3

def setup_scene():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except:
        scene.render.engine = 'BLENDER_EEVEE'
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.render_samples = 64
    else:
        scene.eevee.taa_render_samples = 64
    
    # Clear lights/cams
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()

def setup_lighting():
    # Key Light: [0, -3, 2], intensity 1.0 (approx 500W in Blender)
    bpy.ops.object.light_add(type='POINT', location=(0, -3, 2))
    key = bpy.context.object
    key.data.energy = 800
    
    # Fill Light: [-2, -2, 1.5], intensity 0.5
    bpy.ops.object.light_add(type='POINT', location=(-2, -2, 1.5))
    fill = bpy.context.object
    fill.data.energy = 400
    
    # Rim Light: [0, -5, 3], intensity 0.3
    # Note: User said [0, -5, 3] which is in front (if facing -Y). 
    # I'll use [0, 3, 3] for a RIM light if they face -Y, 
    # BUT I will follow user's coordinates exactly as requested.
    bpy.ops.object.light_add(type='POINT', location=(0, -5, 3))
    rim = bpy.context.object
    rim.data.energy = 300

def setup_camera(mesh_obj):
    h = mesh_obj.dimensions.z
    face_z = h * 0.92
    
    # Medium-Full shot (zoom so face fills frame but outfit is visible)
    # I'll use a slightly wide focal length or just back up.
    bpy.ops.object.camera_add(location=(0, -3.5, face_z), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.data.lens = 50 # Standard lens
    
    # Rotate slightly to see full body? 
    # User said "focused on face and full body outfit".
    # I'll use vertical resolution to capture both.
    bpy.context.scene.render.resolution_y = 1920
    bpy.context.scene.render.resolution_x = 1080

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    setup_scene()
    setup_materials(mesh)
    setup_lighting()
    setup_camera(mesh)
    
    bpy.context.scene.render.filepath = OUTPUT_PATH
    print(f"Rendering to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    print("Render complete.")

if __name__ == "__main__":
    run()
