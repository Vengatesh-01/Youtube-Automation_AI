import os
import subprocess
import json
import uuid
import datetime
from utils import safe_print

# Blender installation path - Set specifically for user system
BLENDER_EXECUTABLE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

ASSETS_DIR = "assets"
BLENDER_ASSET = os.path.join(ASSETS_DIR, "character.blend")

def validate_blender_asset():
    """
    Checks if character.blend exists and contains required actions and shape keys.
    Returns (bool, str).
    """
    if not os.path.exists(BLENDER_ASSET):
        return False, f"Error: assets/character.blend not found."

    safe_print(f"🔍 [Blender] Validating character asset: {BLENDER_ASSET}...")

    # Internal script to check for actions and shape keys
    check_script = """
import bpy
import json
import sys

# Collect actions
actions = [a.name for a in bpy.data.actions]

# Collect shape keys from all meshes
shape_keys = set()
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks:
            shape_keys.add(key.name)

result = {
    "actions": actions,
    "shape_keys": list(shape_keys)
}
print("VALIDATION_DATA_START")
print(json.dumps(result))
print("VALIDATION_DATA_END")
"""
    
    cmd = [BLENDER_EXECUTABLE, "-b", BLENDER_ASSET, "--python-expr", check_script]
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            return False, f"❌ [Blender] Failed to open character asset for validation. Check if the file is a valid .blend file."
        
        output = process.stdout
        if "VALIDATION_DATA_START" not in output:
            return False, "❌ [Blender] Validation script failed to return data."
            
        json_str = output.split("VALIDATION_DATA_START")[1].split("VALIDATION_DATA_END")[0].strip()
        data = json.loads(json_str)
        
        # Check Actions
        required_actions = ["Idle", "Walk", "Sit"]
        missing_actions = [a for a in required_actions if not any(a.lower() in act.lower() for act in data["actions"])]
        if missing_actions:
            return False, f"❌ [Blender] Character asset missing required action(s): {', '.join(missing_actions)}"
            
        # Check Shape Keys
        required_keys = ["Jaw", "Blink"]
        missing_keys = [k for k in required_keys if not any(k.lower() in key.lower() for key in data["shape_keys"])]
        if missing_keys:
            return False, f"❌ [Blender] Character asset missing required shape key(s): {', '.join(missing_keys)}"

        safe_print("Character asset loaded successfully.")
        return True, "Validation successful"
        
    except Exception as e:
        return False, f"❌ [Blender] Validation error: {str(e)}"

def generate_blender_video(script_scenes, voice_file, output_path):
    """
    Generates a 3D animated video using Blender in headless mode.
    - script_scenes: Dict from extract_scenes containing 'visual_prompt'.
    - voice_file: Path to the generated audio (.mp3 or .wav).
    - output_path: Where the final .mp4 should be saved.
    """
    # 0. Validate Assets
    success, message = validate_blender_asset()
    if not success:
        safe_print(message)
        safe_print("🛑 [Blender] Character staging failed. Stopping execution.")
        return False

    safe_print(f"🎬 [Blender] Preparing background animation for {output_path}...")
    
    # 1. Prepare configuration payload for the bpy script
    config = {
        "voice_file": os.path.abspath(voice_file),
        "output_path": os.path.abspath(output_path),
        "scenes": script_scenes
    }
    
    config_path = os.path.abspath(f"temp_blender_config_{uuid.uuid4().hex[:8]}.json")
    with open(config_path, "w") as f:
        json.dump(config, f)

    # 2. Write the Python script that Blender will execute internally
    blender_script_template = """
import bpy
import json
import os
import math

# --- 1. Load Configuration ---
config_path = r"{{CONFIG_PATH}}"
with open(config_path, "r") as f:
    config = json.load(f)

voice_file = config["voice_file"]
output_path = config["output_path"]
scenes = config["scenes"]

# --- 2. Setup Render Settings (9:16 Vertical Shorts) ---
scene = bpy.context.scene
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = output_path

# --- 3. Scene Setup (Camera & Lighting) ---
# Clear existing cameras and lights to avoid duplicates
for obj in bpy.data.objects:
    if obj.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(obj, do_unlink=True)

# Add Camera
bpy.ops.object.camera_add(location=(0, -5, 1.5), rotation=(math.radians(90), 0, 0))
camera = bpy.context.object
scene.camera = camera

# Three-point Lighting
# Key Light
bpy.ops.object.light_add(type='POINT', location=(3, -3, 3))
key_light = bpy.context.object
key_light.data.energy = 1000

# Fill Light
bpy.ops.object.light_add(type='POINT', location=(-3, -2, 2))
fill_light = bpy.context.object
fill_light.data.energy = 400

# Back Light
bpy.ops.object.light_add(type='POINT', location=(0, 3, 3))
back_light = bpy.context.object
back_light.data.energy = 600

# --- 4. Add Audio to Sequencer ---
if not scene.sequence_editor:
    scene.sequence_editor_create()

# Clear existing strips
for strip in scene.sequence_editor.sequences_all:
    scene.sequence_editor.sequences.remove(strip)

audio_strip = scene.sequence_editor.sequences.new_sound(
    name="Voiceover", 
    filepath=voice_file, 
    channel=1, 
    frame_start=1
)

# Set frame end to match audio duration
scene.frame_end = int(audio_strip.frame_duration)

# --- 5. Character Animation & Lip Sync ---
# Find the character armature/mesh
character_mesh = None
armature = None
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        character_mesh = obj
    if obj.type == 'ARMATURE':
        armature = obj

if character_mesh:
    shape_keys = character_mesh.data.shape_keys
    
    # 5a. Lip Sync (Bake Sound to F-Curves)
    jaw_key = None
    for key in shape_keys.key_blocks:
        name = key.name.lower()
        if "jaw" in name or "mouth_open" in name or "open" in name or "mouth" in name:
            jaw_key = key
            break
            
    if jaw_key:
        jaw_key.value = 0.0
        jaw_key.keyframe_insert(data_path='value', frame=1)
        
        # Save current area type to restore later
        original_area = bpy.context.area.type
        
        # We need a window context for some operators
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    override = {'window': window, 'screen': screen, 'area': area, 'scene': scene}
                    # Small hack for headless mode: try to bake directly
                    try:
                        bpy.ops.graph.sound_bake(override, filepath=voice_file, low=(100.0), high=(100000.0))
                    except:
                        # Fallback for headless
                        try:
                            bpy.ops.graph.sound_bake(filepath=voice_file, low=(100.0), high=(100000.0))
                        except Exception as e:
                            print(f"[Blender Script] Sound bake failed: {e}")
                    break

    # 5b. Procedural Blinking
    blink_key = None
    for key in shape_keys.key_blocks:
        name = key.name.lower()
        if "blink" in name or "eyes_closed" in name:
            blink_key = key
            break
            
    if blink_key:
        import random
        frame = 1
        while frame < scene.frame_end:
            blink_key.value = 0.0
            blink_key.keyframe_insert(data_path='value', frame=frame)
            frame += random.randint(60, 150)
            if frame >= scene.frame_end: break
            blink_key.value = 1.0
            blink_key.keyframe_insert(data_path='value', frame=frame)
            frame += 3
            blink_key.value = 0.0
            blink_key.keyframe_insert(data_path='value', frame=frame)

# 5c. Body Animation (Idle/Walk/Sit)
if armature and armature.animation_data:
    armature.animation_data.action = None
    scene_duration_frames = scene.frame_end // max(1, len(scenes))
    current_frame = 1
    
    for scene_label, scene_data in scenes.items():
        prompt = (scene_data.get("visual_prompt", "") + " " + scene_data.get("text", "")).lower()
        
        desired_action = "Idle"
        if any(word in prompt for word in ["walk", "run", "moving", "approach"]): 
            desired_action = "Walk"
        elif any(word in prompt for word in ["sit", "chair", "explain calmly", "table"]): 
            desired_action = "Sit"
        
        action_to_play = None
        for act in bpy.data.actions:
            if desired_action.lower() in act.name.lower():
                action_to_play = act
                break
                
        if not action_to_play and bpy.data.actions:
            action_to_play = bpy.data.actions[0]
            
        if action_to_play:
             if not armature.animation_data.nla_tracks:
                 track = armature.animation_data.nla_tracks.new()
             else:
                 track = armature.animation_data.nla_tracks[0]
                 
             end_frame = min(current_frame + scene_duration_frames, scene.frame_end)
             try:
                strip = track.strips.new(name=desired_action, start=int(current_frame), action=action_to_play)
                action_len = strip.action_frame_end - strip.action_frame_start
                if action_len > 0:
                    strip.repeat = (end_frame - current_frame) / action_len
             except:
                pass
        current_frame += scene_duration_frames

# --- 6. Render Animation ---
print(f"[Blender Script] Rendering frames 1 to {scene.frame_end}...")
bpy.ops.render.render(animation=True)
print("[Blender Script] Render complete.")
"""
    blender_script_content = blender_script_template.replace("{{CONFIG_PATH}}", config_path)

    
    script_path = os.path.abspath(f"temp_blender_script_{uuid.uuid4().hex[:8]}.py")
    with open(script_path, "w") as f:
        f.write(blender_script_content)

    # 3. Execute Blender in background mode
    # Format: blender -b assets/character.blend -P temp_script.py
    cmd = [
        BLENDER_EXECUTABLE,
        "-b",
        BLENDER_ASSET,
        "-P", script_path
    ]

    try:
        # Run subprocess and wait for completion
        safe_print(f"🚀 [Blender] Starting external render process...")
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if process.returncode != 0:
            safe_print("❌ [Blender] Error during render:")
            err_msg = str(process.stderr)
            safe_print(err_msg[-2000:] if len(err_msg) > 2000 else err_msg)
            return False
            
        safe_print("✅ [Blender] Video rendered successfully.")
        return True
    except FileNotFoundError:
        safe_print(f"❌ [Blender] Fatal Error: Blender executable not found at '{BLENDER_EXECUTABLE}'.")
        return False
    finally:
        # Clean up temp files
        if os.path.exists(config_path):
            os.remove(config_path)
        if os.path.exists(script_path):
            os.remove(script_path)

# Startup check for asset presence
if __name__ == "__main__":
    # Internal test of validation logic when run directly
    success, message = validate_blender_asset()
    if not success:
        # We don't safe_print here because the function already does it if successful, 
        # but if it fails we want to show the specific error requested by user.
        # Actually message already contains "Error: assets/character.blend not found."
        safe_print(f"FAILED: {message}")
    else:
        safe_print("Character asset is ready for use.")
else:
    # Optional: Run a light check on import if needed, 
    # but usually preferred to call explicitly from main.
    pass
