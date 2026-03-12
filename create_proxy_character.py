import bpy
import os

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Create high-quality Suzanne as a proxy character
bpy.ops.mesh.primitive_monkey_add(size=2, location=(0,0,1))
char = bpy.context.object
char.name = "Character_Mesh"

# Add Subdivision for Pixar look
subsurf = char.modifiers.new(name="Subsurf", type='SUBSURF')
subsurf.levels = 2
bpy.ops.object.shade_smooth()

# Add basic material
mat = bpy.data.materials.new(name="Pixar_Skin")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.5, 0.4, 1) # Skin tone
char.data.materials.append(mat)

# Add Shape Keys for diagnostics
char.shape_key_add(name="Basis")
char.shape_key_add(name="Jaw")
char.shape_key_add(name="Blink")

# Create Armature
bpy.ops.object.armature_add(location=(0,0,0))
arm = bpy.context.object
arm.name = "Character_Armature"

# Add basic actions for the agent to find
for act_name in ["Idle", "Walk", "Sit", "Talk"]:
    act = bpy.data.actions.new(name=act_name)
    act.use_fake_user = True # Ensure actions are saved!

# Save
os.makedirs("assets", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath="assets/character.blend")
print("SUCCESS: Character mesh and armature created in assets/character.blend")
