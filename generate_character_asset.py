import bpy
import bmesh
import os
import math

def log(msg):
    print(f"[CHAR_GEN] {msg}")

def create_material(name, diffuse_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = diffuse_color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

# 1. Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Create Armature
log("Creating Armature...")
bpy.ops.object.armature_add(location=(0, 0, 0))
armature_obj = bpy.context.object
armature_obj.name = "CharacterArmature"
armature = armature_obj.data
armature.name = "CharacterRig"

bpy.ops.object.mode_set(mode='EDIT')
edit_bones = armature.edit_bones

spine = edit_bones["Bone"]
spine.name = "spine"
spine.head = (0, 0, 0)
spine.tail = (0, 0, 1)

head_bone = edit_bones.new("head")
head_bone.head = (0, 0, 1)
head_bone.tail = (0, 0, 1.6)
head_bone.parent = spine

jaw = edit_bones.new("jaw")
jaw.head = (0, 0, 1.2)
jaw.tail = (0, 0.2, 1.2)
jaw.parent = head_bone

# Arms
arm_l = edit_bones.new("arm.L")
arm_l.head = (0.2, 0, 0.9)
arm_l.tail = (0.7, 0, 0.9)
arm_l.parent = spine

arm_r = edit_bones.new("arm.R")
arm_r.head = (-0.2, 0, 0.9)
arm_r.tail = (-0.7, 0, 0.9)
arm_r.parent = spine

# Legs
leg_l = edit_bones.new("leg.L")
leg_l.head = (0.2, 0, 0)
leg_l.tail = (0.2, 0, -1.0)
leg_l.parent = spine

leg_r = edit_bones.new("leg.R")
leg_r.head = (-0.2, 0, 0)
leg_r.tail = (-0.2, 0, -1.0)
leg_r.parent = spine

bpy.ops.object.mode_set(mode='OBJECT')

# 3. Create Mesh Components
log("Creating Character Mesh Components...")

# Materials
skin_mat = create_material("Skin", (1.0, 0.8, 0.6, 1.0))
suit_mat = create_material("Suit", (0.1, 0.1, 0.3, 1.0)) # Dark blue professional
shirt_mat = create_material("Shirt", (1.0, 1.0, 1.0, 1.0))
glass_mat = create_material("Glass", (0.0, 0.0, 0.0, 1.0), roughness=0.1, metallic=0.5)

# Body (Suit)
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.0, location=(0, 0, 0.5))
body = bpy.context.object
body.name = "Body"
body.data.materials.append(suit_mat)

# Head
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, 0, 1.4))
head = bpy.context.object
head.name = "Head"
head.data.materials.append(skin_mat)

# Shirt/Collar
bpy.ops.mesh.primitive_cylinder_add(radius=0.36, depth=0.1, location=(0,0,0.95))
collar = bpy.context.object
collar.data.materials.append(shirt_mat)

# Glasses
bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=(0.18, -0.4, 1.5), rotation=(1.57, 0, 0))
glass_l = bpy.context.object
glass_l.data.materials.append(glass_mat)

bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=(-0.18, -0.4, 1.5), rotation=(1.57, 0, 0))
glass_r = bpy.context.object
glass_r.data.materials.append(glass_mat)

# Bridge of glasses
bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0, -0.4, 1.5))
bridge = bpy.context.object
bridge.scale = (4, 0.2, 0.2)
bridge.data.materials.append(glass_mat)

# Join All
bpy.ops.object.select_all(action='DESELECT')
for obj in [body, head, collar, glass_l, glass_r, bridge]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
character_mesh = body
character_mesh.name = "CharacterMesh"

# 4. Rigging
log("Rigging mesh to armature...")
character_mesh.select_set(True)
armature_obj.select_set(True)
bpy.context.view_layer.objects.active = armature_obj
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# 5. Shape Keys
log("Adding Shape Keys...")
bpy.context.view_layer.objects.active = character_mesh
bpy.ops.object.mode_set(mode='OBJECT')
character_mesh.shape_key_add(name="Basis")

def add_shape_key(name, move_verts=False):
    sk = character_mesh.shape_key_add(name=name, from_mix=False)
    if move_verts:
        # Very simple deformation: Move some vertices based on Z
        for i, vert in enumerate(character_mesh.data.vertices):
            if vert.co.z > 1.3 and vert.co.y < -0.3: # Face area
                sk.data[i].co.y -= 0.05 # Push mouth area forward/open-ish
    return sk

for key in ["A", "E", "O", "U", "M", "Blink"]:
    add_shape_key(key, move_verts=(key != "Blink"))

# 6. Actions
log("Creating Actions...")
def create_complex_action(name, bone_frames):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    for bone_name, frames in bone_frames.items():
        pb = armature_obj.pose.bones.get(bone_name)
        if pb:
            pb.rotation_mode = 'XYZ'
            for f, val in frames:
                pb.rotation_euler = val
                pb.keyframe_insert(data_path="rotation_euler", frame=f)
    return action

# Idle: breathing + slight head move
create_complex_action("Idle", {
    "spine": [(1, (0,0,0)), (30, (0.02,0,0)), (60, (0,0,0))],
    "head":  [(1, (0,0,0)), (30, (0,0,0.02)), (60, (0,0,0))]
})

# Walk: leg swing
create_complex_action("Walk", {
    "leg.L": [(1, (0.4,0,0)), (15, (-0.4,0,0)), (30, (0.4,0,0))],
    "leg.R": [(1, (-0.4,0,0)), (15, (0.4,0,0)), (30, (-0.4,0,0))],
    "arm.L": [(1, (-0.2,0,0)), (15, (0.2,0,0)), (30, (-0.2,0,0))]
})

# Sit: base pose
create_complex_action("Sit", {
    "spine": [(1, (0.2, 0, 0))],
    "leg.L": [(1, (1.2, 0, 0))],
    "leg.R": [(1, (1.2, 0, 0))]
})

# Talk: jaw + head move
create_complex_action("Talk", {
    "jaw":  [(1, (0,0,0)), (5, (0.2,0,0)), (10, (0,0,0))],
    "head": [(1, (0,0,0)), (10, (0.05, 0.05, 0)), (20, (0,0,0))]
})

# 7. Save
os.makedirs("assets", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath="assets/character.blend")
log("Done! Professional character saved to assets/character.blend")
