import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/facial_features_preview.png")
OUTPUT_BLEND = INPUT_BLEND
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
    except:
        scene.render.engine = 'BLENDER_EEVEE'
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.render_samples = 64
    else:
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 64

def create_mix_node(nodes, links, fac_in, color1_in, color2_in):
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    links.new(fac_in, mix.inputs[0])
    
    # Color 1
    if isinstance(color1_in, (Vector, tuple, list)):
        mix.inputs[6].default_value = color1_in
    else:
        links.new(color1_in, mix.inputs[6])
    
    # Color 2
    if isinstance(color2_in, (Vector, tuple, list)):
        mix.inputs[7].default_value = color2_in
    else:
        links.new(color2_in, mix.inputs[7])
    
    return mix.outputs[2]

def setup_face_material():
    skin_mat = bpy.data.materials.get("Skin_Mat")
    if not skin_mat:
        skin_mat = bpy.data.materials.new("Skin_Mat")
    
    skin_mat.use_nodes = True
    nodes = skin_mat.node_tree.nodes
    links = skin_mat.node_tree.links
    nodes.clear()
    
    # Colors
    skin_color = hex_to_rgb("#F2C29B")
    lip_color = hex_to_rgb("#C97F7F")
    iris_color = hex_to_rgb("#5A341C")
    
    # Essential Nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs[0].default_value = skin_color
    bsdf.inputs[6].default_value = 0.0 # Metallic
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    
    def create_eye_mask(side_sign):
        mapping = nodes.new('ShaderNodeMapping')
        # Precise placement for Meshy stylized head
        mapping.inputs[1].default_value = (0.05 * side_sign, -0.12, 1.7)
        mapping.inputs[3].default_value = (1.0, 1.0, 1.0)
        
        grad = nodes.new('ShaderNodeTexGradient')
        grad.gradient_type = 'SPHERICAL'
        
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'LINEAR'
        # Elements: Pupil, Iris, Sclera, Mask
        ramp.color_ramp.elements[0].position = 0.02
        ramp.color_ramp.elements[0].color = (0,0,0,1)
        
        e1 = ramp.color_ramp.elements.new(0.021); e1.color = iris_color
        e2 = ramp.color_ramp.elements.new(0.04); e2.color = iris_color
        e3 = ramp.color_ramp.elements.new(0.041); e3.color = (1,1,1,1)
        e4 = ramp.color_ramp.elements.new(0.08); e4.color = (1,1,1,1)
        e5 = ramp.color_ramp.elements.new(0.081); e5.color = (0,0,0,0)
        
        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
        links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
        return ramp

    eye_r = create_eye_mask(1)
    eye_l = create_eye_mask(-1)
    
    # Lips
    lip_map = nodes.new('ShaderNodeMapping')
    lip_map.inputs[1].default_value = (0, -0.12, 1.62)
    lip_map.inputs[3].default_value = (2.5, 1.0, 1.0) # Horizontal stretch
    lip_grad = nodes.new('ShaderNodeTexGradient')
    lip_grad.gradient_type = 'SPHERICAL'
    lip_ramp = nodes.new('ShaderNodeValToRGB')
    lip_ramp.color_ramp.elements[0].position = 0.0; lip_ramp.color_ramp.elements[0].color = lip_color
    lip_ramp.color_ramp.elements[1].position = 0.04; lip_ramp.color_ramp.elements[1].color = (0,0,0,0)
    
    links.new(tex_coord.outputs['Object'], lip_map.inputs['Vector'])
    links.new(lip_map.outputs['Vector'], lip_grad.inputs['Vector'])
    links.new(lip_grad.outputs['Fac'], lip_ramp.inputs['Fac'])
    
    # Layering Logic
    # 0. Base Skin
    # 1. Add Lips
    res1 = create_mix_node(nodes, links, lip_ramp.outputs[1], skin_color, lip_ramp.outputs[0])
    # 2. Add Eye R
    res2 = create_mix_node(nodes, links, eye_r.outputs[1], res1, eye_r.outputs[0])
    # 3. Add Eye L
    res3 = create_mix_node(nodes, links, eye_l.outputs[1], res2, eye_l.outputs[0])
    
    links.new(res3, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    setup_scene()
    setup_face_material()
    
    # Render Setup
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()
    
    h = mesh.dimensions.z
    face_z = h * 0.93
    
    bpy.ops.object.light_add(type='POINT', location=(0, -1.5, face_z))
    key = bpy.context.object
    key.data.energy = 600
    
    bpy.ops.object.camera_add(location=(0, -0.6, face_z), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.data.lens = 85
    
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080
    
    print(f"Rendering facial features to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print("Character with refined facial features saved.")

if __name__ == "__main__":
    run()
