import bpy
import os
import math

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/facial_features_final.png")
OUTPUT_BLEND = INPUT_BLEND
os.makedirs("outputs", exist_ok=True)

def srgb_to_linearrgb(c):
    if c < 0.04045: return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (srgb_to_linearrgb(r/255), srgb_to_linearrgb(g/255), srgb_to_linearrgb(b/255), 1.0)

def setup_face():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mat = bpy.data.materials.get("Skin_Mat")
    if not mat: mat = bpy.data.materials.new("Skin_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Colors
    skin_color = hex_to_rgb("#F2C29B")
    lip_color = hex_to_rgb("#C97F7F")
    iris_color = hex_to_rgb("#5A341C")
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs[0].default_value = skin_color
    bsdf.inputs[6].default_value = 0.0
    bsdf.inputs[2].default_value = 0.6
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex_coord.outputs['Object'], sep.inputs[0])
    
    # helper for distance mask
    def create_mask(cx, cy, cz, rx, ry, rz):
        # (x-cx)^2 / rx^2 + ...
        sub_x = nodes.new('ShaderNodeMath'); sub_x.operation = 'SUBTRACT'
        sub_x.inputs[1].default_value = cx
        links.new(sep.outputs[0], sub_x.inputs[0])
        sq_x = nodes.new('ShaderNodeMath'); sq_x.operation = 'MULTIPLY'
        links.new(sub_x.outputs[0], sq_x.inputs[0]); links.new(sub_x.outputs[0], sq_x.inputs[1])
        
        sub_z = nodes.new('ShaderNodeMath'); sub_z.operation = 'SUBTRACT'
        sub_z.inputs[1].default_value = cz
        links.new(sep.outputs[2], sub_z.inputs[0])
        sq_z = nodes.new('ShaderNodeMath'); sq_z.operation = 'MULTIPLY'
        links.new(sub_z.outputs[0], sq_z.inputs[0]); links.new(sub_z.outputs[0], sq_z.inputs[1])
        
        add = nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        links.new(sq_x.outputs[0], add.inputs[0])
        links.new(sq_z.outputs[0], add.inputs[1])
        
        # Less than threshold
        lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
        lt.inputs[1].default_value = rx * rx
        links.new(add.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    # Mix Helper
    def mix_rgba(fac, c1, c2):
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        links.new(fac, mix.inputs[0])
        mix.inputs[6].default_value = c1 if isinstance(c1, tuple) else (0,0,0,1)
        if not isinstance(c1, tuple): links.new(c1, mix.inputs[6])
        mix.inputs[7].default_value = c2 if isinstance(c2, tuple) else (0,0,0,1)
        if not isinstance(c2, tuple): links.new(c2, mix.inputs[7])
        return mix.outputs[2]

    # Layers with Depth Masking (only front -Y)
    y_mask = nodes.new('ShaderNodeMath'); y_mask.operation = 'LESS_THAN'
    y_mask.inputs[1].default_value = -0.08 # Only very front
    links.new(sep.outputs[1], y_mask.inputs[0])
    
    # 1. Lips (Center)
    # cx, cy, cz, rx, ry, rz
    lip_mask_raw = create_mask(0, -0.1, 1.55, 0.02, 0.02, 0.01) 
    lip_mask = nodes.new('ShaderNodeMath'); lip_mask.operation = 'MULTIPLY'
    links.new(lip_mask_raw, lip_mask.inputs[0]); links.new(y_mask.outputs[0], lip_mask.inputs[1])
    res_lips = mix_rgba(lip_mask.outputs[0], skin_color, lip_color)
    
    # 2. Eye R Sclera
    eye_r_sclera_raw = create_mask(0.04, -0.1, 1.66, 0.015, 0.015, 0.025)
    eye_r_sclera = nodes.new('ShaderNodeMath'); eye_r_sclera.operation = 'MULTIPLY'
    links.new(eye_r_sclera_raw, eye_r_sclera.inputs[0]); links.new(y_mask.outputs[0], eye_r_sclera.inputs[1])
    res_eyer1 = mix_rgba(eye_r_sclera.outputs[0], res_lips, (1,1,1,1))
    
    # Eye R Iris
    eye_r_iris_raw = create_mask(0.04, -0.1, 1.66, 0.008, 0.008, 0.01)
    eye_r_iris = nodes.new('ShaderNodeMath'); eye_r_iris.operation = 'MULTIPLY'
    links.new(eye_r_iris_raw, eye_r_iris.inputs[0]); links.new(y_mask.outputs[0], eye_r_iris.inputs[1])
    res_eyer2 = mix_rgba(eye_r_iris.outputs[0], res_eyer1, iris_color)
    
    # 3. Eye L Sclera
    eye_l_sclera_raw = create_mask(-0.04, -0.1, 1.66, 0.015, 0.015, 0.025)
    eye_l_sclera = nodes.new('ShaderNodeMath'); eye_l_sclera.operation = 'MULTIPLY'
    links.new(eye_l_sclera_raw, eye_l_sclera.inputs[0]); links.new(y_mask.outputs[0], eye_l_sclera.inputs[1])
    res_eyel1 = mix_rgba(eye_l_sclera.outputs[0], res_eyer2, (1,1,1,1))
    
    # Eye L Iris
    eye_l_iris_raw = create_mask(-0.04, -0.1, 1.66, 0.008, 0.008, 0.01)
    eye_l_iris = nodes.new('ShaderNodeMath'); eye_l_iris.operation = 'MULTIPLY'
    links.new(eye_l_iris_raw, eye_l_iris.inputs[0]); links.new(y_mask.outputs[0], eye_l_iris.inputs[1])
    res_eyel2 = mix_rgba(eye_l_iris.outputs[0], res_eyel1, iris_color)

    links.new(res_eyel2, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])
    
    # Render verify
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.filepath = OUTPUT_PATH
    
    # Camera Close-up
    for o in bpy.data.objects:
        if o.type == 'CAMERA': o.location = (0, -0.6, 1.7)
    
    print(f"Rendering final face to {OUTPUT_PATH}...")
    bpy.ops.render.render(write_still=True)
    
    bpy.ops.wm.save_as_mainfile(filepath=INPUT_BLEND)

if __name__ == "__main__":
    setup_face()
