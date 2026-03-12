import os
import subprocess
import json
import uuid
import datetime
from utils import safe_print

# Blender installation path - Set specifically for user system
BLENDER_EXECUTABLE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

ASSETS_DIR = "assets"
BLENDER_ASSET = os.path.abspath(os.path.join(ASSETS_DIR, "character.blend"))

def validate_blender_asset():
    """
    Checks if character.blend exists and contains required actions and shape keys.
    Returns (bool, str).
    """
    if not os.path.exists(BLENDER_ASSET):
        return False, f"Error: assets/character.blend not found."

    safe_print(f"[Blender] Validating character asset: {BLENDER_ASSET}...")

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
            return False, f"[Blender] Failed to open character asset for validation. Check if the file is a valid .blend file."
        
        output = process.stdout
        if "VALIDATION_DATA_START" not in output:
            return False, "[Blender] Validation script failed to return data."
            
        json_str = output.split("VALIDATION_DATA_START")[1].split("VALIDATION_DATA_END")[0].strip()
        data = json.loads(json_str)
        
        # Check Actions
        required_actions = ["Idle", "Walk", "Sit"]
        missing_actions = [a for a in required_actions if not any(a.lower() in act.lower() for act in data["actions"])]
        if missing_actions:
            return False, f"[Blender] Character asset missing required action(s): {', '.join(missing_actions)}"
            
        # Check Shape Keys
        required_keys = ["Jaw", "Blink"]
        missing_keys = [k for k in required_keys if not any(k.lower() in key.lower() for key in data["shape_keys"])]
        if missing_keys:
            return False, f"[Blender] Character asset missing required shape key(s): {', '.join(missing_keys)}"

        safe_print("Character asset loaded successfully.")
        return True, "Validation successful"
        
    except Exception as e:
        return False, f"[Blender] Validation error: {str(e)}"

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
        safe_print("[Blender] Character staging failed. Stopping execution.")
        return False

    safe_print(f"[Blender] Preparing background animation for {output_path}...")
    
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
import random
import sys

def log(msg):
    print(f"[Blender Script] {msg}")
    sys.stdout.flush()

try:
    log("Starting internal Blender script...")
config_path = r"{{CONFIG_PATH}}"
if not os.path.exists(config_path):
    print(f"ERROR: Config not found at {config_path}")
    exit(1)

with open(config_path, "r") as f:
    config = json.load(f)

voice_file = config["voice_file"]
output_path = config["output_path"]
scenes = config["scenes"]

# --- 2. Setup Render Settings (Cinematic Shorts) ---
scene = bpy.context.scene
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.constant_rate_factor = 'PERCEPTUALLY_LOSSLESS'
scene.render.filepath = output_path

# Use CYCLES for better headless/CPU compatibility
scene.render.engine = 'CYCLES'
# Force CPU for stability in headless environments
bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'NONE'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16 # Very low for speed
scene.render.film_transparent = False

# --- 3. Scene Setup (World & Lighting) ---
if not scene.world:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs[0].default_value = (0.05, 0.05, 0.08, 1.0) # Dark cinematic blue

# --- 3. Scene Setup (Camera & Lighting) ---
# Clear existing junk
for obj in bpy.data.objects:
    if obj.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(obj, do_unlink=True)

# Add Cinematic Camera
bpy.ops.object.camera_add(location=(0, -4, 1.6), rotation=(math.radians(90), 0, 0))
camera = bpy.context.object
scene.camera = camera
camera.data.lens = 50 # Cinematic focal length
camera.data.use_dof = True
camera.data.dof.focus_distance = 4.0
camera.data.dof.aperture_fstop = 1.8 # Soft background

# Professional 3-Point Area Lighting
# Key Light (Large Area Light for soft shadows)
bpy.ops.object.light_add(type='AREA', location=(2.5, -3, 3), rotation=(math.radians(45), 0, math.radians(45)))
key_light = bpy.context.object
key_light.data.energy = 500
key_light.data.size = 2.0

# Fill Light
bpy.ops.object.light_add(type='AREA', location=(-2.5, -2, 2.5), rotation=(math.radians(45), 0, math.radians(-45)))
fill_light = bpy.context.object
fill_light.data.energy = 200
fill_light.data.size = 3.0

# Back Light (Rim Light)
bpy.ops.object.light_add(type='AREA', location=(0, 3, 3), rotation=(math.radians(135), 0, 0))
back_light = bpy.context.object
back_light.data.energy = 800
back_light.data.size = 1.5

# --- 3b. Emotional Lighting Preset Function ---
def apply_lighting_preset(emotion, world, lights):
    emotion = emotion.lower()
    bg = world.node_tree.nodes.get('Background')
    if not bg: return
    
    if "sad" in emotion:
        bg.inputs[0].default_value = (0.02, 0.02, 0.05, 1.0) # Deep moody blue
        lights[0].data.energy = 200 # Key
        lights[1].data.energy = 50 # Fill
        lights[2].data.energy = 100 # Rim
    elif "hope" in emotion or "sunrise" in emotion:
        bg.inputs[0].default_value = (0.2, 0.08, 0.05, 1.0) # Warm orange
        lights[0].data.color = (1.0, 0.8, 0.6)
        lights[0].data.energy = 700
    elif "success" in emotion or "determined" in emotion:
        bg.inputs[0].default_value = (0.1, 0.1, 0.1, 1.0) # Neutral
        lights[0].data.energy = 800
        lights[2].data.energy = 1200 # Strong Rim for "hero" look
    elif "think" in emotion:
        bg.inputs[0].default_value = (0.05, 0.05, 0.08, 1.0)
        lights[0].data.energy = 400

# --- 4. Add Audio to Sequencer ---
if not scene.sequence_editor:
    scene.sequence_editor_create()

for strip in scene.sequence_editor.sequences_all:
    scene.sequence_editor.sequences.remove(strip)

audio_strip = scene.sequence_editor.sequences.new_sound(
    name="Voiceover", 
    filepath=voice_file, 
    channel=1, 
    frame_start=1
)
scene.frame_end = int(audio_strip.frame_duration)

# --- 5. Character Animation Logic ---
character_mesh = None
armature = None
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        character_mesh = obj
    if obj.type == 'ARMATURE':
        armature = obj

# Helper: Apply Shape Key
def set_shape_key(key_name, value, frame):
    if not character_mesh or not character_mesh.data.shape_keys: return
    for kb in character_mesh.data.shape_keys.key_blocks:
        if key_name.lower() in kb.name.lower():
            kb.value = value
            kb.keyframe_insert(data_path='value', frame=frame)
            return True
    return False

if character_mesh:
    # 5a. Lip Sync (Bake Sound)
    jaw_key = None
    for key in character_mesh.data.shape_keys.key_blocks:
        if "jaw" in key.name.lower() or "mouth_open" in key.name.lower():
            jaw_key = key
            break
            
    if jaw_key:
        jaw_key.value = 0.0
        jaw_key.keyframe_insert(data_path='value', frame=1)
        try:
            bpy.ops.graph.sound_bake(filepath=voice_file, low=(100.0), high=(10000.0))
        except Exception as e:
            print(f"Sound bake error: {e}")

    # 5b. Procedural Blinking
    frame = 1
    while frame < scene.frame_end:
        set_shape_key("blink", 0.0, frame)
        frame += random.randint(45, 120)
        if frame >= scene.frame_end: break
        set_shape_key("blink", 1.0, frame) # Close
        set_shape_key("blink", 0.0, frame + 3) # Open
        frame += 4

# 5c. Scene-by-Scene Director Logic
if armature and armature.animation_data:
    if not armature.animation_data.nla_tracks:
        track = armature.animation_data.nla_tracks.new()
    else:
        track = armature.animation_data.nla_tracks[0]

    current_frame = 1
    avg_scene_dur = scene.frame_end // max(1, len(scenes))
    
    for scene_idx, (m_id, s_data) in enumerate(scenes.items()):
        prompt = (s_data.get("visual_prompt", "") + " " + s_data.get("text", "")).lower()
        duration = avg_scene_dur
        end_frame = min(current_frame + duration, scene.frame_end)
        
        # 1. Lighting Preset
        apply_lighting_preset(s_data.get("emotion", "Neutral"), scene.world, [key_light, fill_light, back_light])
        
        # 2. Determine Action
        action_name = s_data.get("action", "Idle")
        if not any(a.lower() in action_name.lower() for a in ["Walk", "Sit", "Talk", "Idle", "Gesture", "Stand"]):
            # Fallback to fuzzy match
            if "walk" in prompt: action_name = "Walk"
            elif "sit" in prompt: action_name = "Sit"
            elif "talk" in prompt or "gesture" in prompt: action_name = "Talk"
            else: action_name = "Idle"

        # Apply Action in NLA
        selected_act = None
        for act in bpy.data.actions:
            if action_name.lower() in act.name.lower():
                selected_act = act
                break
        
        if selected_act:
            strip = track.strips.new(name=action_name, start=int(current_frame), action=selected_act)
            act_len = strip.action_frame_end - strip.action_frame_start
            if act_len > 0:
                strip.repeat = (end_frame - current_frame) / act_len
            strip.extrapolation = 'HOLD_FORWARD'
            strip.blend_type = 'REPLACE'

        # 3. Apply Emotion
        emotion_key = s_data.get("emotion", "Neutral")
        set_shape_key(emotion_key, 1.0, current_frame + 10)
        set_shape_key(emotion_key, 0.0, end_frame - 5)

        # 4. Camera Movement Logic
        cam_instr = s_data.get("camera", "").upper()
        if "ZOOM" in cam_instr:
            camera.location = (0, -5, 1.6)
            camera.keyframe_insert(data_path="location", frame=current_frame)
            camera.location = (0, -3, 1.6)
            camera.keyframe_insert(data_path="location", frame=end_frame)
        elif "LOW" in cam_instr:
            camera.location = (0, -3.5, 0.6)
            camera.rotation_euler[0] = math.radians(100)
            camera.keyframe_insert(data_path="location", frame=current_frame)
            camera.keyframe_insert(data_path="rotation_euler", frame=current_frame)
        elif "CLOSE" in cam_instr or "FACE" in cam_instr:
            camera.location = (0, -1.8, 1.7) # Close to head
            camera.keyframe_insert(data_path="location", frame=current_frame)
        elif "TRACK" in cam_instr:
            camera.location = (-1.5, -4, 1.6)
            camera.keyframe_insert(data_path="location", frame=current_frame)
            camera.location = (1.5, -4, 1.6)
            camera.keyframe_insert(data_path="location", frame=end_frame)
        else: # Default STATIC-ish with focus
            camera.location = (0, -4, 1.6)
            camera.rotation_euler = (math.radians(90), 0, 0)
            camera.keyframe_insert(data_path="location", frame=current_frame)
            camera.keyframe_insert(data_path="rotation_euler", frame=current_frame)

        # Always re-focus on character
        camera.data.dof.focus_object = armature if armature else None
        
        current_frame = end_frame

    log(f"Rendering {scene.frame_end} frames...")
    bpy.ops.render.render(animation=True)
    log("Render complete.")
except Exception as e:
    import traceback
    log(f"FATAL ERROR in Blender script: {str(e)}")
    log(traceback.format_exc())
    sys.exit(1)
"""
    blender_script_content = blender_script_template.replace("{{CONFIG_PATH}}", config_path)

    
    script_path = os.path.abspath(f"temp_blender_script_{uuid.uuid4().hex[:8]}.py")
    with open(script_path, "w") as f:
        f.write(blender_script_content)

    # 3. Execute Blender in background mode
    # Format: blender -b assets/character.blend -P temp_script.py
    cmd = [
        os.path.abspath(BLENDER_EXECUTABLE),
        "-b",
        os.path.abspath(BLENDER_ASSET),
        "-P", os.path.abspath(script_path)
    ]

    try:
        # Run subprocess and wait for completion
        log_agent = safe_print # Fallback for this module
        log_agent(f"[Blender] Starting external render process...")
        log_agent(f"Executing: {' '.join(cmd)}")
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        
        if process.returncode != 0:
            safe_print("[Blender] Error during render:")
            err_msg = str(process.stderr)
            with open("blender_render.log", "w", encoding="utf-8") as f:
                f.write("--- STDOUT ---\n")
                f.write(process.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(process.stderr)
            safe_print(err_msg[-2000:] if len(err_msg) > 2000 else err_msg)
            return False
            
        with open("blender_render.log", "w", encoding="utf-8") as f:
            f.write(process.stdout)
            
        safe_print("✅ [Blender] Video rendered successfully.")
        return True
    except FileNotFoundError:
        safe_print(f"[Blender] Fatal Error: Blender executable not found at '{BLENDER_EXECUTABLE}'.")
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
