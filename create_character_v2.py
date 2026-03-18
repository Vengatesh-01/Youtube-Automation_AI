"""
create_character_v2.py
Run with: blender -b -P create_character_v2.py
Creates a fully rigged anime-style character with:
  - CharacterMesh with all lip-sync and expression shape keys
  - CharacterRig (armature)
  - Basic PBR materials
  - Neutral lighting setup
  - Camera
Saves to: assets/character_v2.blend
"""

import bpy
import math
import os

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_character_mesh():
    """Create a stylized anime head + body mesh."""
    # --- HEAD ---
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=32, ring_count=16, location=(0, 0, 1.65))
    head = bpy.context.object
    head.name = "CharacterMesh"
    head.scale = (0.9, 0.8, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # --- BODY ---
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.9, location=(0, 0, 0.9))
    body = bpy.context.object
    body.name = "Body"

    # --- EYES (empties for saccades) ---
    for side, x in [("L", 0.18), ("R", -0.18)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(x, -0.42, 1.73))
        eye = bpy.context.object
        eye.name = f"Eye_{side}"

    # --- Join all into CharacterMesh ---
    bpy.ops.object.select_all(action='DESELECT')
    for ob_name in ["CharacterMesh", "Body", "Eye_L", "Eye_R"]:
        obj = bpy.data.objects.get(ob_name)
        if obj:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["CharacterMesh"]
    bpy.ops.object.join()
    mesh_obj = bpy.context.object
    mesh_obj.name = "CharacterMesh"
    return mesh_obj

def add_shape_keys(mesh_obj):
    """Add all required lip-sync and expression shape keys."""
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)

    # Basis (required first)
    bpy.ops.object.shape_key_add(from_mix=False)
    mesh_obj.data.shape_keys.key_blocks[0].name = "Basis"

    shape_key_names = [
        # Lip-sync phonemes
        "AI",    # Vowel A and I  → wide open mouth
        "E",     # Vowel E        → slight open, spread
        "O",     # Vowel O        → round open
        "U",     # Vowel U        → pursed lips
        "MBP",   # M/B/P sounds   → closed lips pressed
        "FV",    # F/V sounds     → upper teeth on lower lip
        # Expressions
        "blink",
        "blink_L",
        "blink_R",
        "smile",
        "frown",
        "neutral",
        # Breathing (used by animate_character)
        "mouth_open",
    ]

    for name in shape_key_names:
        bpy.ops.object.shape_key_add(from_mix=False)
        key = mesh_obj.data.shape_keys.key_blocks[-1]
        key.name = name
        key.value = 0.0

    print(f"✅ Shape keys added: {[k.name for k in mesh_obj.data.shape_keys.key_blocks]}")
    return mesh_obj.data.shape_keys

def create_material(mesh_obj):
    """Build a basic PBR skin material."""
    mat = bpy.data.materials.new(name="AnimeCharacterMat")
    mat.use_nodes = True  # Deprecated in 6.0 but still works in 5.0
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.92, 0.78, 0.68, 1.0)  # Skin tone
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3

    mesh_obj.data.materials.append(mat)
    print("✅ PBR material applied.")

def create_armature(mesh_obj):
    """Create a simple anime character armature and parent the mesh."""
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm_obj = bpy.context.object
    arm_obj.name = "CharacterRig"
    arm = arm_obj.data
    arm.name = "CharacterRig"

    bpy.ops.object.mode_set(mode='EDIT')
    bones = arm.edit_bones

    # Root (hip) bone
    root = bones[0]
    root.name = "root"
    root.head = (0, 0, 0.7)
    root.tail = (0, 0, 0.9)

    # Spine
    spine = bones.new("spine")
    spine.head = (0, 0, 0.9)
    spine.tail = (0, 0, 1.3)
    spine.parent = root

    # Chest
    chest = bones.new("chest")
    chest.head = (0, 0, 1.3)
    chest.tail = (0, 0, 1.5)
    chest.parent = spine

    # Neck
    neck = bones.new("neck")
    neck.head = (0, 0, 1.5)
    neck.tail = (0, 0, 1.6)
    neck.parent = chest

    # Head
    head_bone = bones.new("head")
    head_bone.head = (0, 0, 1.6)
    head_bone.tail = (0, 0, 1.9)
    head_bone.parent = neck

    # Jaw
    jaw = bones.new("jaw")
    jaw.head = (0, -0.1, 1.62)
    jaw.tail = (0, -0.25, 1.55)
    jaw.parent = head_bone

    # Arms
    for side, sign in [("L", 1), ("R", -1)]:
        upper = bones.new(f"upper_arm_{side}")
        upper.head = (sign * 0.3, 0, 1.45)
        upper.tail = (sign * 0.55, 0, 1.15)
        upper.parent = chest

        lower = bones.new(f"lower_arm_{side}")
        lower.head = (sign * 0.55, 0, 1.15)
        lower.tail = (sign * 0.75, 0, 0.9)
        lower.parent = upper

    # Legs
    for side, sign in [("L", 1), ("R", -1)]:
        upper = bones.new(f"upper_leg_{side}")
        upper.head = (sign * 0.12, 0, 0.7)
        upper.tail = (sign * 0.14, 0, 0.35)
        upper.parent = root

        lower = bones.new(f"lower_leg_{side}")
        lower.head = (sign * 0.14, 0, 0.35)
        lower.tail = (sign * 0.14, 0, 0.02)
        lower.parent = upper

    bpy.ops.object.mode_set(mode='OBJECT')

    # Parent mesh to armature with automatic weights
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    print("✅ Armature created and parented.")
    return arm_obj

def add_idle_animation(arm_obj, total_frames=720):
    """Add basic idle: breathing via bone location keyframes."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames

    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode='POSE')
    import math as m

    chest_pbone = arm_obj.pose.bones.get("chest")
    if chest_pbone:
        for f in range(1, total_frames, 8):
            chest_pbone.location[2] = m.sin(f * 0.1) * 0.008
            chest_pbone.keyframe_insert(data_path="location", frame=f, index=2)
        print("✅ Idle breathing animation added.")

    bpy.ops.object.mode_set(mode='OBJECT')

def setup_scene_and_camera():
    """Add lighting and camera for vertical-format rendering."""
    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    # Engine (Blender 5.0 uses BLENDER_EEVEE, earlier used BLENDER_EEVEE_NEXT)
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    for candidate in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        if candidate in engines:
            scene.render.engine = candidate
            break

    # Camera
    bpy.ops.object.camera_add(location=(0, -4.0, 1.65), rotation=(math.radians(90), 0, 0))
    cam = bpy.context.object
    cam.name = "Camera"
    cam.data.lens = 50
    scene.camera = cam

    # Key light
    bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
    key = bpy.context.object
    key.name = "KeyLight"
    key.data.energy = 400
    key.data.color = (1.0, 0.95, 0.85)

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-2, -1, 2))
    fill = bpy.context.object
    fill.name = "FillLight"
    fill.data.energy = 120
    fill.data.color = (0.6, 0.7, 1.0)

    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 2, 3))
    rim = bpy.context.object
    rim.name = "RimLight"
    rim.data.energy = 200
    rim.data.color = (0.4, 0.6, 1.0)

    print("✅ Scene, camera, and 3-point lighting configured.")

def main():
    output_path = os.path.abspath("assets/character_v2.blend")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("🎭 Creating anime character rig...")
    clear_scene()
    mesh_obj = create_character_mesh()
    add_shape_keys(mesh_obj)
    create_material(mesh_obj)
    arm_obj = create_armature(mesh_obj)
    add_idle_animation(arm_obj)
    setup_scene_and_camera()

    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\n🏆 character_v2.blend saved to: {output_path}")
    print(f"   Objects: {[o.name for o in bpy.data.objects]}")
    print(f"   Shape keys: {[k.name for k in mesh_obj.data.shape_keys.key_blocks]}")

main()
