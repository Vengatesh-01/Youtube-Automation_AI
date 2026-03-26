import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/facial_features_cinematic.png")
OUTPUT_BLEND = INPUT_BLEND
os.makedirs("outputs", exist_ok=True)

def srgb_to_linearrgb(c):
    if c < 0.04045: return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (srgb_to_linearrgb(r/255), srgb_to_linearrgb(g/255), srgb_to_linearrgb(b/255), 1.0)

def find_face_anchor(mesh_obj):
    vgroup = mesh_obj.vertex_groups.get("Head")
    if not vgroup: return Vector((0, -0.1, 1.7))
    verts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices if any(g.group == vgroup.index for g in v.groups)]
    if not verts: return Vector((0, -0.1, 1.7))
    return min(verts, key=lambda p: p.y)

def setup_face_material(anchor):
    mat = bpy.data.materials.get("Skin_Mat")
    if not mat: mat = bpy.data.materials.new("Skin_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Precise Colors
    skin_color = hex_to_rgb("#F2C29B")
    iris_base = hex_to_rgb("#4A2C1D")
    iris_light = hex_to_rgb("#6B442E") # Lighter gradient
    highlight_color = (1, 1, 1, 1)
    brow_color = hex_to_rgb("#2A1C14")
    lip_color = hex_to_rgb("#C97F7F")
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs[0].default_value = skin_color
    bsdf.inputs[6].default_value = 0.0
    bsdf.inputs[2].default_value = 0.5 # Slightly smoother skin
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex_coord.outputs['Object'], sep.inputs[0])
    
    Ax, Ay, Az = anchor

    def create_mask(cx, cz, rx, rz):
        sub_x = nodes.new('ShaderNodeMath'); sub_x.operation = 'SUBTRACT'; sub_x.inputs[1].default_value = cx
        links.new(sep.outputs[0], sub_x.inputs[0])
        sq_x = nodes.new('ShaderNodeMath'); sq_x.operation = 'MULTIPLY'
        links.new(sub_x.outputs[0], sq_x.inputs[0]); links.new(sub_x.outputs[0], sq_x.inputs[1])
        sub_z = nodes.new('ShaderNodeMath'); sub_z.operation = 'SUBTRACT'; sub_z.inputs[1].default_value = cz
        links.new(sep.outputs[2], sub_z.inputs[0])
        sq_z = nodes.new('ShaderNodeMath'); sq_z.operation = 'MULTIPLY'
        links.new(sub_z.outputs[0], sq_z.inputs[0]); links.new(sub_z.outputs[0], sq_z.inputs[1])
        add = nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        links.new(sq_x.outputs[0], add.inputs[0]); links.new(sq_z.outputs[0], add.inputs[1])
        lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = rx * rz
        links.new(add.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    def mix_rgba(fac, c1, c2):
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'; links.new(fac, mix.inputs[0])
        mix.inputs[6].default_value = c1 if isinstance(c1, tuple) else (0,0,0,1)
        if not isinstance(c1, tuple): links.new(c1, mix.inputs[6])
        mix.inputs[7].default_value = c2 if isinstance(c2, tuple) else (0,0,0,1)
        if not isinstance(c2, tuple): links.new(c2, mix.inputs[7])
        return mix.outputs[2]

    # Depth Mask (Front Only)
    y_mask = nodes.new('ShaderNodeMath'); y_mask.operation = 'LESS_THAN'
    y_mask.inputs[1].default_value = Ay + 0.02
    links.new(sep.outputs[1], y_mask.inputs[0])

    # 1. Lips
    lip_mask_raw = create_mask(Ax, Az - 0.08, 0.015, 0.008)
    lip_mask = nodes.new('ShaderNodeMath'); lip_mask.operation = 'MULTIPLY'
    links.new(lip_mask_raw, lip_mask.inputs[0]); links.new(y_mask.outputs[0], lip_mask.inputs[1])
    res1 = mix_rgba(lip_mask.outputs[0], skin_color, lip_color)
    
    # 2. Eyes Logic (Iterative layering)
    eye_z = Az + 0.025
    eye_x_off = 0.035
    
    def add_eye(base_color, side):
        ex = Ax + (eye_x_off * side)
        # Sclera
        sclera = create_mask(ex, eye_z, 0.02, 0.03)
        res_s = mix_rgba(sclera, base_color, (1,1,1,1))
        # Iris (Gradient simulation with a darkening at the top)
        iris_mask = create_mask(ex, eye_z, 0.012, 0.015)
        # Vertical gradient for iris
        z_grad = nodes.new('ShaderNodeMath'); z_grad.operation = 'SUBTRACT'
        z_grad.inputs[1].default_value = eye_z
        links.new(sep.outputs[2], z_grad.inputs[0])
        # Mix iris base and light
        i_mix = nodes.new('ShaderNodeMix'); i_mix.data_type = 'RGBA'
        i_mix.inputs[0].default_value = 0.5 # Default mix
        i_mix.inputs[6].default_value = iris_base
        i_mix.inputs[7].default_value = iris_light
        res_i = mix_rgba(iris_mask, res_s, i_mix.outputs[2])
        # Pupil
        pupil_mask = create_mask(ex, eye_z, 0.004, 0.005)
        res_p = mix_rgba(pupil_mask, res_i, (0,0,0,1))
        # Highlight (White dot top-right)
        high_mask = create_mask(ex + 0.004, eye_z + 0.006, 0.002, 0.002)
        res_h = mix_rgba(high_mask, res_p, highlight_color)
        return res_h

    res2 = add_eye(res1, 1) # Right
    res3 = add_eye(res2, -1) # Left
    
    # 3. Eyebrows (Thin and Elongated)
    # Mask: Scale down Z and scale up X inside create_mask or separate logic
    def create_brow_mask(bx, bz):
        sub_x = nodes.new('ShaderNodeMath'); sub_x.operation = 'SUBTRACT'; sub_x.inputs[1].default_value = bx
        links.new(sep.outputs[0], sub_x.inputs[0])
        sq_x = nodes.new('ShaderNodeMath'); sq_x.operation = 'MULTIPLY'
        links.new(sub_x.outputs[0], sq_x.inputs[0]); links.new(sub_x.outputs[0], sq_x.inputs[1])
        # Scale X up for elongation
        sc_x = nodes.new('ShaderNodeMath'); sc_x.operation = 'MULTIPLY'; sc_x.inputs[1].default_value = 0.5 
        links.new(sq_x.outputs[0], sc_x.inputs[0])
        
        sub_z = nodes.new('ShaderNodeMath'); sub_z.operation = 'SUBTRACT'; sub_z.inputs[1].default_value = bz
        links.new(sep.outputs[2], sub_z.inputs[0])
        sq_z = nodes.new('ShaderNodeMath'); sq_z.operation = 'MULTIPLY'
        links.new(sub_z.outputs[0], sq_z.inputs[0]); links.new(sub_z.outputs[0], sq_z.inputs[1])
        # Scale Z down for thinness
        sc_z = nodes.new('ShaderNodeMath'); sc_z.operation = 'MULTIPLY'; sc_z.inputs[1].default_value = 10.0
        links.new(sq_z.outputs[0], sc_z.inputs[0])
        
        add = nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        links.new(sc_x.outputs[0], add.inputs[0]); links.new(sc_z.outputs[0], add.inputs[1])
        lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.0002
        links.new(add.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    brow_mask_r = create_brow_mask(Ax + 0.04, Az + 0.08)
    res4 = mix_rgba(brow_mask_r, res3, brow_color)
    brow_mask_l = create_brow_mask(Ax - 0.04, Az + 0.08)
    res5 = mix_rgba(brow_mask_l, res4, brow_color)

    links.new(res5, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    anchor = find_face_anchor(mesh)
    setup_face_material(anchor)
    
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080
    
    # Final production lighting
    bpy.ops.object.select_all(action='DESELECT')
    for l in bpy.data.objects:
        if l.type == 'LIGHT': l.select_set(True)
    bpy.ops.object.delete()
    
    bpy.ops.object.light_add(type='POINT', location=(0.5, -1.5, anchor.z + 0.2))
    bpy.context.object.data.energy = 600
    bpy.ops.object.light_add(type='POINT', location=(-0.5, -1.5, anchor.z - 0.2))
    bpy.context.object.data.energy = 300
    
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

if __name__ == "__main__":
    run()
