import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/refined_eyes_final.png")
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

def setup_refined_face(anchor):
    mat = bpy.data.materials.get("Skin_Mat")
    if not mat: mat = bpy.data.materials.new("Skin_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Colors
    skin_color = hex_to_rgb("#F2C29B")
    iris_base = hex_to_rgb("#4A2C1D")
    iris_light = hex_to_rgb("#6B442E")
    brow_color = hex_to_rgb("#5A341C") 
    lip_color = hex_to_rgb("#C97F7F")
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs[0].default_value = skin_color
    bsdf.inputs[6].default_value = 0.0
    
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

    # Y Mask
    y_mask = nodes.new('ShaderNodeMath'); y_mask.operation = 'LESS_THAN'
    y_mask.inputs[1].default_value = Ay + 0.02
    links.new(sep.outputs[1], y_mask.inputs[0])

    # 1. PRESERVE Lips
    lip_mask_raw = create_mask(Ax, Az - 0.08, 0.015, 0.008)
    lip_mask = nodes.new('ShaderNodeMath'); lip_mask.operation = 'MULTIPLY'
    links.new(lip_mask_raw, lip_mask.inputs[0]); links.new(y_mask.outputs[0], lip_mask.inputs[1])
    res1 = mix_rgba(lip_mask.outputs[0], skin_color, lip_color)
    
    # 2. REFINED Eyes
    eye_z = Az + 0.02
    eye_x_off = 0.028 # Narrower spacing (closer to nose)
    
    def add_eye(base_color, side):
        ex = Ax + (eye_x_off * side)
        # Sclera (Sharp Oval)
        sclera = create_mask(ex, eye_z, 0.01, 0.016)
        res_s = mix_rgba(sclera, base_color, (1,1,1,1))
        # Iris (Gradient)
        iris_mask = create_mask(ex, eye_z, 0.007, 0.01)
        res_i = mix_rgba(iris_mask, res_s, iris_base)
        # Pupil
        pupil = create_mask(ex, eye_z, 0.003, 0.004)
        res_p = mix_rgba(pupil, res_i, (0,0,0,1))
        # Highlights (Top-right)
        high = create_mask(ex + 0.003, eye_z + 0.004, 0.002, 0.002)
        res_h = mix_rgba(high, res_p, (1,1,1,1))
        # Eyelashes (Thin top arc)
        lash = create_mask(ex, eye_z + 0.008, 0.012, 0.001)
        res_l = mix_rgba(lash, res_h, (0,0,0,1))
        return res_l

    res2 = add_eye(res1, 1)
    res3 = add_eye(res2, -1)
    
    # 3. PRESERVE Curved Eyebrows
    def create_curved_brow(bx, bz):
        dx = nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'; dx.inputs[1].default_value = bx
        links.new(sep.outputs[0], dx.inputs[0])
        curv = nodes.new('ShaderNodeMath'); curv.operation = 'MULTIPLY'
        links.new(dx.outputs[0], curv.inputs[0]); links.new(dx.outputs[0], curv.inputs[1])
        sc_c = nodes.new('ShaderNodeMath'); sc_c.operation = 'MULTIPLY'; sc_c.inputs[1].default_value = 4.0
        links.new(curv.outputs[0], sc_c.inputs[0])
        nz = nodes.new('ShaderNodeMath'); nz.operation = 'ADD'
        links.new(sep.outputs[2], nz.inputs[0]); links.new(sc_c.outputs[0], nz.inputs[1])
        sub_nz = nodes.new('ShaderNodeMath'); sub_nz.operation = 'SUBTRACT'; sub_nz.inputs[1].default_value = bz
        links.new(nz.outputs[0], sub_nz.inputs[0])
        sq_nz = nodes.new('ShaderNodeMath'); sq_nz.operation = 'MULTIPLY'
        links.new(sub_nz.outputs[0], sq_nz.inputs[0]); links.new(sub_nz.outputs[0], sq_nz.inputs[1])
        sc_z = nodes.new('ShaderNodeMath'); sc_z.operation = 'MULTIPLY'; sc_z.inputs[1].default_value = 25.0
        links.new(sq_nz.outputs[0], sc_z.inputs[0])
        sq_dx = nodes.new('ShaderNodeMath'); sq_dx.operation = 'MULTIPLY'
        links.new(dx.outputs[0], sq_dx.inputs[0]); links.new(dx.outputs[0], sq_dx.inputs[1])
        sc_x = nodes.new('ShaderNodeMath'); sc_x.operation = 'MULTIPLY'; sc_x.inputs[1].default_value = 0.4
        links.new(sq_dx.outputs[0], sc_x.inputs[0])
        add = nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        links.new(sc_x.outputs[0], add.inputs[0]); links.new(sc_z.outputs[0], add.inputs[1])
        lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.00015
        links.new(add.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    brow_r = create_curved_brow(Ax + 0.035, Az + 0.065)
    res4 = mix_rgba(brow_r, res3, brow_color)
    brow_l = create_curved_brow(Ax - 0.035, Az + 0.065)
    res5 = mix_rgba(brow_l, res4, brow_color)

    links.new(res5, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    anchor = find_face_anchor(mesh)
    setup_refined_face(anchor)
    
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080
    
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

if __name__ == "__main__":
    run()
