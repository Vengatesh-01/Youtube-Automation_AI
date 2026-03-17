import bpy
import bmesh
import os
import math
import random
import sys

def log(msg):
    print(f"[BLENDER_AUTO] {msg}")
    sys.stdout.flush()

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    log("Scene cleared.")

def create_material(name, diffuse_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # Check if Base Color is an input (standard for Principled BSDF)
        bsdf.inputs[0].default_value = diffuse_color
        bsdf.inputs[7].default_value = roughness
        bsdf.inputs[4].default_value = metallic
    return mat

def setup_camera_and_render():
    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 30
    
    # Eevee engine check
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, "RenderSettings") and "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items else 'BLENDER_EEVEE'
    
    # Setup Render Format (Forcing PNG for now to bypass FFMPEG headless issues)
    scene.render.image_settings.file_format = 'PNG'
    log("Selected format: PNG (forced)")
    
    if False: # Skip FFmpeg settings
        pass
    
    if scene.render.image_settings.file_format in ['FFMPEG', 'FFMPEG_VIDEO']:
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.ffmpeg.audio_codec = 'AAC'
        scene.render.ffmpeg.constant_rate_factor = 'PERCEPTUALLY_LOSSLESS'
    
    # Add Vertical Camera
    bpy.ops.object.camera_add(location=(0, -8, 1.2), rotation=(math.radians(90), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    log(f"Camera setup: 1080x1920, {scene.render.engine}")

def build_character_armature():
    log("Building Armature Skeleton...")
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm_obj = bpy.context.object
    arm_obj.name = "CharacterRig"
    arm_data = arm_obj.data
    
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    
    # Remove default bone
    if "Bone" in eb: eb.remove(eb["Bone"])
    
    # Central chain
    bones = [
        ("root", (0, 0, 0), (0, 0, 0.1), None),
        ("spine", (0, 0, 0.1), (0, 0, 0.6), "root"),
        ("neck", (0, 0, 0.6), (0, 0, 0.7), "spine"),
        ("head", (0, 0, 0.7), (0, 0, 1.1), "neck"),
    ]
    
    for name, head, tail, parent in bones:
        b = eb.new(name)
        b.head, b.tail = head, tail
        if parent: b.parent = eb[parent]

    # Symmetric bones
    for side, sgn in [("L", 1), ("R", -1)]:
        # Arms
        sh = eb.new(f"shoulder.{side}")
        sh.head, sh.tail = (0, 0, 0.55), (0.2 * sgn, 0, 0.55)
        sh.parent = eb["spine"]
        
        ua = eb.new(f"upper_arm.{side}")
        ua.head, ua.tail = (0.2 * sgn, 0, 0.55), (0.45 * sgn, 0, 0.55)
        ua.parent = sh
        
        fa = eb.new(f"forearm.{side}")
        fa.head, fa.tail = (0.45 * sgn, 0, 0.55), (0.7 * sgn, 0, 0.55)
        fa.parent = ua
        
        h = eb.new(f"hand.{side}")
        h.head, h.tail = (0.7 * sgn, 0, 0.55), (0.8 * sgn, 0, 0.55)
        h.parent = fa
        
        # Legs
        th = eb.new(f"thigh.{side}")
        th.head, th.tail = (0.15 * sgn, 0, 0.1), (0.15 * sgn, 0, -0.4)
        th.parent = eb["root"]
        
        sh = eb.new(f"shin.{side}")
        sh.head, sh.tail = (0.15 * sgn, 0, -0.4), (0.15 * sgn, 0, -0.8)
        sh.parent = th
        
        ft = eb.new(f"foot.{side}")
        ft.head, ft.tail = (0.15 * sgn, 0, -0.8), (0.15 * sgn, -0.2, -0.8)
        ft.parent = sh

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def build_cartoon_character():
    log("Building Cartoon Character Parts...")
    parts = {}
    skin_mat = create_material("Skin", (1.0, 0.8, 0.6, 1.0))
    cloth_mat = create_material("Cloth", (0.2, 0.3, 0.8, 1.0))
    
    # Head & Torso
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.5, location=(0, 0, 0.35))
    parts["torso"] = bpy.context.object
    parts["torso"].name = "Torso"; parts["torso"].data.materials.append(cloth_mat)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0.9))
    parts["head"] = bpy.context.object
    parts["head"].name = "Head"; parts["head"].data.materials.append(skin_mat)
    
    # Limbs
    limb_config = [
        ("upper_arm", 0.32, 0.55, 0.22, 0.08, cloth_mat),
        ("forearm", 0.57, 0.55, 0.22, 0.07, cloth_mat),
        ("hand", 0.75, 0.55, 0.1, 0.1, skin_mat),
        ("thigh", 0.15, -0.15, 0.09, 0.45, cloth_mat),
        ("shin", 0.15, -0.6, 0.08, 0.4, cloth_mat),
        ("foot", 0.15, -0.82, 0.1, 0.05, skin_mat),
    ]
    
    for name, off_x, off_z, size_x, size_z, mat in limb_config:
        for side, sgn in [("L", 1), ("R", -1)]:
            # Simplified box limbs
            full_name = f"{name}.{side}"
            # Adjust location for Y offset (feet)
            y_off = -0.1 if name == "foot" else 0
            bpy.ops.mesh.primitive_cube_add(location=(off_x * sgn, y_off, off_z))
            obj = bpy.context.object
            obj.name = full_name
            obj.scale = (size_x, 0.1, size_z) if "foot" not in name else (size_x, 0.2, size_z)
            obj.data.materials.append(mat)
            parts[full_name] = obj

    return parts

def parent_parts_to_bones(parts, arm_obj):
    log("Parenting parts to bones...")
    for name, obj in parts.items():
        bone_name = "spine" if name == "torso" else name
        if bone_name in arm_obj.data.bones:
            obj.parent = arm_obj
            obj.parent_type = 'BONE'
            obj.parent_bone = bone_name
    log("Parenting complete.")

def setup_facial_expressions(head_obj):
    if not head_obj: return
    log("Setting up shape keys...")
    if not head_obj.data.shape_keys: head_obj.shape_key_add(name="Basis")
    
    keys = ["neutral", "smile", "angry", "sad", "surprised", "blink", "mouth_open", "mouth_wide",
            "AI", "E", "O", "U", "MBP", "FV", "rest"]
    for k in keys:
        if k not in head_obj.data.shape_keys.key_blocks:
            head_obj.shape_key_add(name=k)
    log(f"Added {len(keys)} shape keys.")

def create_animation_actions(arm_obj):
    log("Creating animation actions...")
    def add_action(name, data):
        action = bpy.data.actions.new(name=name)
        action.use_fake_user = True
        for b_name, frames in data.items():
            pb = arm_obj.pose.bones.get(b_name)
            if not pb: continue
            pb.rotation_mode = 'XYZ'
            for f, rot in frames:
                pb.rotation_euler = [math.radians(r) for r in rot]
                pb.keyframe_insert(data_path="rotation_euler", frame=f)
        return action

    # WALKING (24 frame cycle)
    add_action("WALKING", {
        "thigh.L": [(1, (30,0,0)), (12, (-30,0,0)), (24, (30,0,0))],
        "thigh.R": [(1, (-30,0,0)), (12, (30,0,0)), (24, (-30,0,0))],
        "upper_arm.L": [(1, (-20,0,0)), (12, (20,0,0)), (24, (-20,0,0))],
        "upper_arm.R": [(1, (20,0,0)), (12, (-20,0,0)), (24, (20,0,0))],
    })

    # RUNNING (16 frame cycle)
    add_action("RUNNING", {
        "spine": [(1, (15,0,0))],
        "thigh.L": [(1, (50,0,0)), (8, (-50,0,0)), (16, (50,0,0))],
        "thigh.R": [(1, (-50,0,0)), (8, (50,0,0)), (16, (-50,0,0))],
    })

    # SITTING
    add_action("SITTING", {
        "root": [(1, (0,0,-0.5))],
        "thigh.L": [(1, (90,0,0))], "thigh.R": [(1, (90,0,0))],
        "shin.L": [(1, (-90,0,0))], "shin.R": [(1, (-90,0,0))],
    })

    # TALKING
    add_action("TALKING", {
        "head": [(1, (0,0,0)), (10, (5,0,0)), (20, (0,0,0)), (30, (-5,0,0)), (40, (0,0,0))],
    })

    # GESTURES
    add_action("GESTURE_POINT", {"upper_arm.R": [(1, (0,0,0)), (10, (70, -20, 0))]})
    add_action("GESTURE_PALM", {"upper_arm.L": [(1, (0,0,0)), (10, (40, 30, 0))]})

def setup_lip_sync(head_obj, audio_path):
    if not head_obj or not os.path.exists(audio_path):
        log(f"Lip sync skipped: audio not found at {audio_path}")
        return
    log("Baking lip sync...")
    # Select head and insert keyframe for mouth_open
    kb = head_obj.data.shape_keys.key_blocks.get("mouth_open")
    if kb:
        kb.value = 0
        kb.keyframe_insert(data_path='value', frame=1)
        # In a real script, you'd select the F-Curve and run sound_bake
        # bpy.ops.graph.sound_bake(filepath=audio_path)
    log("Lip sync baked (logic placeholder).")

if __name__ == "__main__":
    clear_scene()
    setup_camera_and_render()
    
    arm_obj = build_character_armature()
    parts = build_cartoon_character()
    parent_parts_to_bones(parts, arm_obj)
    
    setup_facial_expressions(parts.get("head"))
    create_animation_actions(arm_obj)
    
    # Save blend file
    output_dir = os.path.join(os.getcwd(), "assets")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "automated_character.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    
    log(f"SUCCESS: Character automation complete. File: {output_path}")
