
import bpy
import os

# 1. Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Create Placeholder Character (Cube)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
character = bpy.context.active_object
character.name = "PlaceholderCharacter"

# 3. Add Shape Keys
character.shape_key_add(name="Basis")
character.shape_key_add(name="Jaw")
character.shape_key_add(name="Blink")

# 4. Add Armature Rig
bpy.ops.object.armature_add(location=(0, 0, 1))
armature = bpy.context.active_object
armature.name = "CharacterArmature"

# Parent mesh to armature
character.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type='OBJECT')

# 5. Create Required Actions
def create_action(obj, name):
    if not obj.animation_data:
        obj.animation_data_create()
    
    action = bpy.data.actions.new(name=name)
    action.use_fake_user = True
    obj.animation_data.action = action
    
    # Simple animation: move up and down
    obj.location[2] = 1.0
    obj.keyframe_insert(data_path="location", frame=1, index=2)
    obj.location[2] = 1.2
    obj.keyframe_insert(data_path="location", frame=15, index=2)
    obj.location[2] = 1.0
    obj.keyframe_insert(data_path="location", frame=30, index=2)
    
    return action

create_action(character, "Idle")
create_action(character, "Walk")
create_action(character, "Sit")

# 6. Save File
assets_dir = os.path.join(os.getcwd(), "assets")
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

save_path = os.path.join(assets_dir, "character.blend")
bpy.ops.wm.save_as_mainfile(filepath=save_path)

print(f"✅ Successfully created: {save_path}")
