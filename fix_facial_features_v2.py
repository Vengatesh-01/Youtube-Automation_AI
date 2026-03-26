import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/facial_features_fixed.png")
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
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene.eevee, "render_samples"):
        scene.eevee.render_samples = 64
    elif hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64

def create_procedural_feature(nodes, links, tex_coord, loc, scale, colors):
    # colors is a list of (position, color) tuples
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs[1].default_value = loc # Precise world/object offset
    mapping.inputs[3].default_value = scale 
    
    grad = nodes.new('ShaderNodeTexGradient')
    grad.gradient_type = 'SPHERICAL'
    
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'LINEAR'
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    
    for i, (pos, color) in enumerate(colors):
        if i == 0:
            ele = ramp.color_ramp.elements[0]
        else:
            ele = ramp.color_ramp.elements.new(pos)
        ele.position = pos
        ele.color = color
        
    links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
    links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    return ramp

def setup_face_material():
    mat = bpy.data.materials.get("Skin_Mat")
    if not mat: mat = bpy.data.materials.new("Skin_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    skin_color = hex_to_rgb("#F2C29B")
    lip_color = hex_to_rgb("#C97F7F")
    iris_color = hex_to_rgb("#5A341C")
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs[0].default_value = skin_color
    bsdf.inputs[6].default_value = 0.0
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    
    # helper for mix
    def mix_layers(fac, bg, fg):
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        links.new(fac, mix.inputs[0])
        if isinstance(bg, (Vector, tuple, list)): mix.inputs[6].default_value = bg
        else: links.new(bg, mix.inputs[6])
        if isinstance(fg, (Vector, tuple, list)): mix.inputs[7].default_value = fg
        else: links.new(fg, mix.inputs[7])
        return mix.outputs[2]

    # Eye R: Sclera(0.1), Iris(0.04), Pupil(0.02)
    # Using 10x scale to keep ovals small
    eye_r_ramp = create_procedural_feature(nodes, links, tex_coord, (0.05, -0.12, 1.7), (10, 10, 10), [
        (0.02, (0,0,0,1)),
        (0.04, iris_color),
        (0.08, (1,1,1,1)),
        (0.081, (0,0,0,0))
    ])
    
    eye_l_ramp = create_procedural_feature(nodes, links, tex_coord, (-0.05, -0.12, 1.7), (10, 10, 10), [
        (0.02, (0,0,0,1)),
        (0.04, iris_color),
        (0.08, (1,1,1,1)),
        (0.081, (0,0,0,0))
    ])
    
    lip_ramp = create_procedural_feature(nodes, links, tex_coord, (0, -0.12, 1.62), (15, 30, 20), [
        (0.04, lip_color),
        (0.05, (0,0,0,0))
    ])
    
    # Layering
    l1 = mix_layers(lip_ramp.outputs[1], skin_color, lip_ramp.outputs[0])
    l2 = mix_layers(eye_r_ramp.outputs[1], l1, eye_r_ramp.outputs[0])
    l3 = mix_layers(eye_l_ramp.outputs[1], l2, eye_l_ramp.outputs[0])
    
    links.new(l3, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    setup_scene()
    setup_face_material()
    
    # Lights refresh
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()
    
    bpy.ops.object.light_add(type='POINT', location=(0, -2, 1.7))
    key = bpy.context.object
    key.data.energy = 800
    
    bpy.ops.object.camera_add(location=(0, -0.7, 1.7), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.data.lens = 85
    
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.filepath = OUTPUT_PATH
    
    print(f"Rendering fixed face to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print("Character with fixed facial features saved.")

if __name__ == "__main__":
    run()
