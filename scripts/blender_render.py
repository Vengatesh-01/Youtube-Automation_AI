import bpy
import json
import os
import math
import random

def setup_scene():
    """Sets up the scene for vertical video (1080x1920) and 24fps with CPU optimizations."""
    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    
    # 🚀 CPU RENDERING OPTIMIZATION
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 1) else 'BLENDER_EEVEE'
    
    # Lower samples for speed
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 12
        scene.eevee.use_bloom = False
        scene.eevee.use_gtao = False
        scene.eevee.use_ssr = False
    
    if hasattr(scene, "eevee"):
        scene.eevee.shadow_cube_size = '512'
        scene.eevee.shadow_cascade_size = '512'

def load_character(blend_path):
    """Loads the character from the .blend template."""
    if not os.path.exists(blend_path):
        return None, None
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    head = bpy.data.objects.get("Character_Mesh")
    armature = bpy.data.objects.get("Character_Armature")
    return head, armature

def apply_lipsync(head_obj, json_path):
    """Applies lip-sync data with smoothing/interpolation."""
    if not head_obj or not head_obj.data.shape_keys: return
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Clear existing keyframes
    head_obj.data.shape_keys.animation_data_clear()
    
    mouth_shapes = data.get("mouthCues", [])
    for i, cue in enumerate(mouth_shapes):
        start_frame = int(cue["start"] * 24)
        end_frame = int(cue["end"] * 24)
        shape_key_name = cue.get("shape_key", "MBP")
        
        key_block = head_obj.data.shape_keys.key_blocks.get(shape_key_name)
        if not key_block: continue

        # Smooth interpolation
        key_block.value = 0.0
        key_block.keyframe_insert(data_path='value', frame=max(0, start_frame - 2))
        key_block.value = 1.0
        key_block.keyframe_insert(data_path='value', frame=start_frame)
        key_block.value = 1.0
        key_block.keyframe_insert(data_path='value', frame=end_frame)
        key_block.value = 0.0
        key_block.keyframe_insert(data_path='value', frame=end_frame + 2)

def animate_character(head_obj, armature, total_frames):
    """Adds organic movements using noise for realism and eye saccades."""
    # 1. Blinking (using the 'blink' shape key)
    if head_obj and head_obj.data.shape_keys:
        blink_key = head_obj.data.shape_keys.key_blocks.get("blink")
        if blink_key:
            f = 10
            while f < total_frames:
                blink_key.value = 0.0
                blink_key.keyframe_insert(data_path="value", frame=f)
                blink_key.value = 1.0
                blink_key.keyframe_insert(data_path="value", frame=f+2)
                blink_key.value = 0.0
                blink_key.keyframe_insert(data_path="value", frame=f+4)
                f += random.randint(60, 144) # 2.5 - 6 seconds @ 24fps

    # 2. 👁️ Micro-Eye Saccades (via small head twitches)
    # 3. 🌊 IDLE SWAY & BREATHING (Organic Drift)
    if armature:
        armature.keyframe_delete(data_path="rotation_euler")
        armature.keyframe_delete(data_path="location")
        for f in range(1, total_frames, 5):
            # Sway + Twitch
            twitch = random.uniform(-0.005, 0.005) if random.random() > 0.92 else 0
            armature.rotation_euler[2] = math.sin(f * 0.05) * 0.02 + twitch
            armature.keyframe_insert(data_path="rotation_euler", frame=f, index=2)
            
            armature.rotation_euler[0] = math.sin(f * 0.03) * 0.01
            armature.keyframe_insert(data_path="rotation_euler", frame=f, index=0)
            
            # Breathing (Z-oscillation)
            armature.location[2] = math.sin(f * 0.1) * 0.008 
            armature.keyframe_insert(data_path="location", frame=f, index=2)

def animate_camera(total_frames):
    """🧠 PATTERN INTERRUPT CAMERA LOGIC (Jump Cuts & FOV shifts)"""
    cam = bpy.data.objects.get("Camera")
    if not cam:
        bpy.ops.object.camera_add(location=(0, -8, 2.7), rotation=(math.radians(90), 0, 0))
        cam = bpy.context.active_object
    
    cam_data = cam.data
    
    # Initial State
    cam.location[1] = -8
    cam.keyframe_insert(data_path="location", frame=1, index=1)
    cam_data.lens = 50
    cam_data.keyframe_insert(data_path="lens", frame=1)

    # 🎬 CINEMATIC DEPTH OF FIELD
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 6.0
    cam_data.dof.aperture_fstop = 1.8

    # Jump Cuts
    f = 1
    while f < total_frames:
        interval = random.randint(100, 180) # 4-7 seconds
        f += interval
        if f >= total_frames: break
        
        # 0=Default, 1=Zoom, 2=Wide
        choice = random.choice([0, 1, 2])
        if choice == 0:
            y_pos, fov = -8.0, 50
        elif choice == 1:
            y_pos, fov = -5.8, 42 # Close up
        else:
            y_pos, fov = -9.5, 65 # Wide

        cam.location[1] = y_pos
        cam_data.lens = fov
        
        cam.keyframe_insert(data_path="location", frame=f, index=1)
        cam_data.keyframe_insert(data_path="lens", frame=f)
        
        # Set to Constant interp
        for fc in cam.animation_data.action.fcurves:
            if fc.data_path == "location":
                fc.keyframe_points[-1].interpolation = 'CONSTANT'
        for fc in cam_data.animation_data.action.fcurves:
            if fc.data_path == "lens":
                fc.keyframe_points[-1].interpolation = 'CONSTANT'

def run_render(audio_path, blend_path, lipsync_path, output_video):
    setup_scene()
    # character_v2.blend has CharacterMesh and CharacterRig
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    head = bpy.data.objects.get("CharacterMesh")
    armature = bpy.data.objects.get("CharacterRig")
    if not head: return
    
    total_frames = 24 * 30 
    bpy.context.scene.frame_end = total_frames
    
    apply_lipsync(head, lipsync_path)
    animate_character(head, armature, total_frames)
    animate_camera(total_frames)
    
    # 5. Background & World
    if os.path.exists("inputs/background.png"):
        # Create background plane
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 5))
        bg = bpy.context.object
        bg.rotation_euler[0] = math.radians(90)
        bg.name = "Background_Plane"
        
        mat = bpy.data.materials.new(name="Background_Mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.abspath("inputs/background.png"))
        mat.node_tree.links.new(tex.outputs[0], bsdf.inputs["Base Color"])
        bg.data.materials.append(mat)

        # ✨ DYNAMIC BACKGROUND MOTION (Slow Pan)
        bg.location[0] = -2
        bg.keyframe_insert(data_path="location", frame=1, index=0)
        bg.location[0] = 2
        bg.keyframe_insert(data_path="location", frame=total_frames, index=0)
    
    if not bpy.context.scene.sequence_editor:
        bpy.context.scene.sequence_editor_create()
    bpy.context.scene.sequence_editor.sequences.new_sound("Audio", audio_path, 3, 1)

    bpy.context.scene.render.filepath = output_video
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.audio_codec = 'AAC'
    
    bpy.ops.render.render(animation=True)

if __name__ == "__main__":
    import sys
    # Handle Blender's special argument passing
    try:
        idx = sys.argv.index("--") + 1
        args = sys.argv[idx:]
        if len(args) >= 4:
            run_render(args[0], args[1], args[2], args[3])
    except ValueError:
        print("Usage: blender -b -P script.py -- <audio> <blend> <sync> <output>")
