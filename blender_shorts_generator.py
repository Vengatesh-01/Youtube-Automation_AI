import bpy
import json
import os
import math
import random

# CONFIG
VOICE_FILE  = os.environ.get("SHORTS_AUDIO",  "")
TOPIC_TITLE = os.environ.get("SHORTS_TOPIC",  "Never Give Up")
OUTPUT_PATH = os.environ.get("SHORTS_OUTPUT", "outputs/final_short.mp4")
CHARACTER_BLEND = "assets/character.blend"

def setup_scene():
    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 1) else 'BLENDER_EEVEE'
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 12

def animate_character(total_frames):
    head = bpy.data.objects.get("Head")
    armature = bpy.data.objects.get("CharacterArmature")
    
    if head and head.data.shape_keys:
        blink_key = head.data.shape_keys.key_blocks.get("Blink")
        if blink_key:
            f = 10
            while f < total_frames:
                blink_key.value = 0.0
                blink_key.keyframe_insert(data_path="value", frame=f)
                blink_key.value = 1.0
                blink_key.keyframe_insert(data_path="value", frame=f+2)
                blink_key.value = 0.0
                blink_key.keyframe_insert(data_path="value", frame=f+4)
                f += random.randint(48, 120)

    if armature:
        armature.keyframe_delete(data_path="rotation_euler")
        for f in range(1, total_frames, 5):
            twitch = random.uniform(-0.005, 0.005) if random.random() > 0.9 else 0
            armature.rotation_euler[2] = math.sin(f * 0.05) * 0.02 + twitch
            armature.keyframe_insert(data_path="rotation_euler", frame=f, index=2)
            armature.rotation_euler[0] = math.sin(f * 0.03) * 0.01
            armature.keyframe_insert(data_path="rotation_euler", frame=f, index=0)

def animate_camera(total_frames):
    cam = bpy.data.objects.get("Camera")
    if not cam: return
    cam_data = cam.data
    f = 1
    while f < total_frames:
        interval = random.randint(100, 180)
        f += interval
        if f >= total_frames: break
        choice = random.choice([0, 1, 2])
        y_pos, fov = (-8.0, 50) if choice == 0 else ((-5.8, 42) if choice == 1 else (-9.5, 65))
        cam.location[1] = y_pos
        cam_data.lens = fov
        cam.keyframe_insert(data_path="location", frame=f, index=1)
        cam_data.keyframe_insert(data_path="lens", frame=f)
        for fc in cam.animation_data.action.fcurves:
            if fc.data_path == "location": fc.keyframe_points[-1].interpolation = 'CONSTANT'

def run_assembly():
    setup_scene()
    if VOICE_FILE and os.path.exists(VOICE_FILE):
        if not bpy.context.scene.sequence_editor: bpy.context.scene.sequence_editor_create()
        audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound("Voice", VOICE_FILE, 3, 1)
        total_frames = audio_strip.frame_final_end
        bpy.context.scene.frame_end = total_frames
    else:
        total_frames = 24 * 15
        bpy.context.scene.frame_end = total_frames

    animate_character(total_frames)
    animate_camera(total_frames)

    # Overlays
    for obj in bpy.data.objects:
        if "Title" in obj.name and hasattr(obj.data, "body"):
            obj.data.body = TOPIC_TITLE.upper()

    bpy.context.scene.render.filepath = os.path.abspath(OUTPUT_PATH)
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.audio_codec = 'AAC'
    
    bpy.ops.render.render(animation=True)

if __name__ == "__main__":
    run_assembly()
