import bpy
import os
import math
from mathutils import Vector

# Config
INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")
OUTPUT_PATH = os.path.abspath("outputs/facial_features_adaptive.png")
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
    
    verts = []
    for v in mesh_obj.data.vertices:
        for g in v.groups:
            if g.group == vgroup.index and g.weight > 0.5:
                verts.append(mesh_obj.matrix_world @ v.co)
                break
    
    if not verts: return Vector((0, -0.1, 1.7))
    
    # Find the most -Y (frontal) point
    frontal = min(verts, key=lambda p: p.y)
    # The eyes should be slightly above the tip of the nose/face anchor
    # Mouth slightly below.
    return frontal

def setup_face_material(anchor):
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
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex_coord.outputs['Object'], sep.inputs[0])
    
    # Anchor: (Ax, Ay, Az)
    Ax, Ay, Az = anchor
    
    def create_mask(cx, cz, rx, rz):
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
        links.new(sq_x.outputs[0], add.inputs[0]); links.new(sq_z.outputs[0], add.inputs[1])
        
        lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
        lt.inputs[1].default_value = rx * rx
        links.new(add.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    def mix_rgba(fac, c1, c2):
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        links.new(fac, mix.inputs[0])
        mix.inputs[6].default_value = c1 if isinstance(c1, tuple) else (0,0,0,1)
        if not isinstance(c1, tuple): links.new(c1, mix.inputs[6])
        mix.inputs[7].default_value = c2 if isinstance(c2, tuple) else (0,0,0,1)
        if not isinstance(c2, tuple): links.new(c2, mix.inputs[7])
        return mix.outputs[2]

    # Y Mask
    y_mask = nodes.new('ShaderNodeMath'); y_mask.operation = 'LESS_THAN'
    y_mask.inputs[1].default_value = Ay + 0.02 # Tiny tolerance
    links.new(sep.outputs[1], y_mask.inputs[0])
    
    # Adaptive placement relative to anchor
    # Anchor is usually nose tip or chin tip if it's the most -Y.
    # Let's assume anchor is centered in X.
    
    # Lips: at anchor Z or slightly above/below?
    # Usually the -Y point is the tip of the nose.
    # Mouth at anchor Z - 0.05
    # Eyes at anchor Z + 0.05
    
    lip_mask_raw = create_mask(Ax, Az - 0.08, 0.02, 0.01)
    lip_mask = nodes.new('ShaderNodeMath'); lip_mask.operation = 'MULTIPLY'
    links.new(lip_mask_raw, lip_mask.inputs[0]); links.new(y_mask.outputs[0], lip_mask.inputs[1])
    res1 = mix_rgba(lip_mask.outputs[0], skin_color, lip_color)
    
    # Eyes
    eye_z = Az + 0.02
    eye_x_off = 0.035
    
    eye_r_sclera = create_mask(Ax + eye_x_off, eye_z, 0.02, 0.03)
    res2 = mix_rgba(eye_r_sclera, res1, (1,1,1,1))
    eye_r_iris = create_mask(Ax + eye_x_off, eye_z, 0.01, 0.01)
    res3 = mix_rgba(eye_r_iris, res2, iris_color)
    
    eye_l_sclera = create_mask(Ax - eye_x_off, eye_z, 0.02, 0.03)
    res4 = mix_rgba(eye_l_sclera, res3, (1,1,1,1))
    eye_l_iris = create_mask(Ax - eye_x_off, eye_z, 0.01, 0.01)
    res5 = mix_rgba(eye_l_iris, res4, iris_color)
    
    links.new(res5, bsdf.inputs[0])
    links.new(bsdf.outputs[0], output.inputs[0])

def run():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    anchor = find_face_anchor(mesh)
    print(f"Face Anchor Found: {anchor}")
    
    setup_face_material(anchor)
    
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'LIGHT', 'CAMERA'}: o.select_set(True)
    bpy.ops.object.delete()
    
    bpy.ops.object.light_add(type='POINT', location=(0, -2, anchor.z))
    bpy.context.object.data.energy = 800
    
    # Closer face shot
    bpy.ops.object.camera_add(location=(0, anchor.y - 0.5, anchor.z), rotation=(1.57, 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080
    
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

if __name__ == "__main__":
    run()
