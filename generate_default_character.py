
import bpy
import os
import math

# 1. Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Create Humanoid Character
# Torso
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.8, location=(0, 0, 1.2))
torso = bpy.context.active_object
torso.name = "Torso"
torso.scale = (0.8, 0.5, 1.2)

# Head
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5, location=(0, 0, 2.7))
head = bpy.context.active_object
head.name = "Head"

# Arms
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0.9, 0, 1.8), rotation=(0, math.radians(15), 0))
r_arm = bpy.context.active_object
r_arm.name = "Arm_R"

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(-0.9, 0, 1.8), rotation=(0, math.radians(-15), 0))
l_arm = bpy.context.active_object
l_arm.name = "Arm_L"

# Legs
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.2, location=(0.4, 0, 0.6))
r_leg = bpy.context.active_object
r_leg.name = "Leg_R"

bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.2, location=(-0.4, 0, 0.6))
l_leg = bpy.context.active_object
l_leg.name = "Leg_L"

# Join parts into one mesh (except head to keep shape keys easy)
bpy.ops.object.select_all(action='DESELECT')
torso.select_set(True)
r_arm.select_set(True)
l_arm.select_set(True)
r_leg.select_set(True)
l_leg.select_set(True)
bpy.context.view_layer.objects.active = torso
bpy.ops.object.join()
character_body = torso
character_body.name = "CharacterBody"

# Head should have shape keys
head.shape_key_add(name="Basis")
head.shape_key_add(name="Jaw")   # Mouth Open
head.shape_key_add(name="Blink") # Eyes Closed

# Simple material
mat = bpy.data.materials.new(name="CharacterMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.5, 0.8, 1.0) # Blueish
character_body.data.materials.append(mat)
head.data.materials.append(mat)

# 4. Add Armature Rig
bpy.ops.object.armature_add(location=(0, 0, 0))
armature = bpy.context.active_object
armature.name = "CharacterArmature"

# Parent mesh to armature
bpy.ops.object.select_all(action='DESELECT')
character_body.select_set(True)
head.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type='OBJECT')

# 5. Create Required Actions (Placeholders for logic)
def create_action(obj, name, move_z=0.2):
    if not obj.animation_data:
        obj.animation_data_create()
    
    action = bpy.data.actions.new(name=name)
    action.use_fake_user = True
    obj.animation_data.action = action
    
    # Simple animation: subtle bounce
    obj.location[2] = 0.0
    obj.keyframe_insert(data_path="location", frame=1, index=2)
    obj.location[2] = move_z
    obj.keyframe_insert(data_path="location", frame=15, index=2)
    obj.location[2] = 0.0
    obj.keyframe_insert(data_path="location", frame=30, index=2)
    
    return action

create_action(armature, "Idle", 0.05)
create_action(armature, "Walk", 0.2)
create_action(armature, "Sit", -0.5)

# 6. Save File
assets_dir = os.path.join(os.getcwd(), "assets")
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

save_path = os.path.join(assets_dir, "character.blend")
bpy.ops.wm.save_as_mainfile(filepath=save_path)

print(f"✅ Successfully created Humanoid Character: {save_path}")
