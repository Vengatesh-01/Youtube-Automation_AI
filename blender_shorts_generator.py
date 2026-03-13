"""
Blender Shorts Generator
========================
Generates a 15-20 second cartoon YouTube Shorts (1080x1920) in Blender background mode.

Usage:
    blender -b assets/character.blend -P blender_shorts_generator.py

Optional args (passed via environment variables):
    SHORTS_AUDIO   : path to voiceover .wav/.mp3 (for lip-sync)
    SHORTS_TOPIC   : topic string for title card  (default: "Never Give Up")
    SHORTS_OUTPUT  : output path                  (default: outputs/shorts.mp4)
"""

import bpy
import os
import sys
import math
import random
import traceback

# ─────────────────────────────────────────────
# 0. CONFIGURATION
# ─────────────────────────────────────────────
VOICE_FILE  = os.environ.get("SHORTS_AUDIO",  "")          # .wav or .mp3
TOPIC_TITLE = os.environ.get("SHORTS_TOPIC",  "Never Give Up")
OUTPUT_PATH = os.environ.get("SHORTS_OUTPUT", "outputs/shorts.mp4")

FPS          = 30
TOTAL_SEC    = random.randint(15, 20)   # 15-20 seconds
TOTAL_FRAMES = FPS * TOTAL_SEC

# Environment choices: "park", "room", "street"
ENV_CHOICE = random.choice(["park", "room", "street"])

os.makedirs(os.path.dirname(OUTPUT_PATH) if os.path.dirname(OUTPUT_PATH) else "outputs", exist_ok=True)

def log(msg):
    print(f"[SHORTS_GEN] {msg}", flush=True)

# ─────────────────────────────────────────────
# 1. RENDER SETTINGS  (Eevee – fast & lightweight)
# ─────────────────────────────────────────────
log("Setting up render settings (Eevee, 1080x1920, 30fps)...")
scene = bpy.context.scene
# Auto-detect Eevee engine name (changed across Blender versions)
# Blender 5.0 uses 'BLENDER_EEVEE', 4.x used 'BLENDER_EEVEE_NEXT'
_valid_engines = {e.identifier for e in bpy.types.RenderEngine.__subclasses__()
                  if hasattr(e, 'identifier')}
# Simpler approach: just try setting it and catch the error
for _engine_name in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = _engine_name
        log(f"Using render engine: {_engine_name}")
        break
    except (TypeError, AttributeError):
        continue

scene.render.resolution_x        = 1080
scene.render.resolution_y        = 1920
scene.render.resolution_percentage = 100
scene.frame_start                = 1
scene.frame_end                  = TOTAL_FRAMES
scene.render.fps                 = FPS

# Output format (FFMPEG for MP4 h264 natively inside Blender)
try:
    scene.render.image_settings.file_format  = 'FFMPEG'
except TypeError:
    try:
        scene.render.image_settings.file_format  = 'FFMPEG_VIDEO'
    except TypeError:
        try:
            scene.render.image_settings.file_format  = 'AVI_JPEG'
        except TypeError:
            log("WARNING: No native video format found in this Blender build! Falling back to PNG sequence.")
            scene.render.image_settings.file_format  = 'PNG'

if 'FFMPEG' in scene.render.image_settings.file_format:
    scene.render.ffmpeg.format               = 'MPEG4'
    scene.render.ffmpeg.codec                = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.audio_codec          = 'AAC'

scene.render.filepath = os.path.abspath(OUTPUT_PATH)

# Eevee quality tweaks
try:
    eevee = scene.eevee
    eevee.use_bloom          = True
    eevee.bloom_intensity    = 0.05
    eevee.use_soft_shadows   = True
    eevee.taa_render_samples = 16    # Enough for cartoon look
except Exception:
    pass

log(f"Scene: {ENV_CHOICE.upper()}, Duration: {TOTAL_SEC}s ({TOTAL_FRAMES} frames)")

# ─────────────────────────────────────────────
# 2. WORLD / SKY
# ─────────────────────────────────────────────
log("Setting up world lighting...")
if not scene.world:
    scene.world = bpy.data.worlds.new("CartoonWorld")
scene.world.use_nodes = True
bg_node = scene.world.node_tree.nodes.get("Background")
if bg_node:
    if ENV_CHOICE == "park":
        bg_node.inputs[0].default_value = (0.4, 0.7, 1.0, 1)  # Sky blue
        bg_node.inputs[1].default_value = 0.8
    elif ENV_CHOICE == "room":
        bg_node.inputs[0].default_value = (0.9, 0.85, 0.8, 1)  # Warm interior
        bg_node.inputs[1].default_value = 0.3
    else:  # street
        bg_node.inputs[0].default_value = (0.25, 0.25, 0.35, 1)  # Evening grey
        bg_node.inputs[1].default_value = 0.5

# ─────────────────────────────────────────────
# 3. CLEAR STALE CAMERAS & LIGHTS
# ─────────────────────────────────────────────
log("Clearing old cameras and lights...")
for obj in list(bpy.data.objects):
    if obj.type in {'CAMERA', 'LIGHT'} or obj.name.startswith("Env_"):
        bpy.data.objects.remove(obj, do_unlink=True)

# ─────────────────────────────────────────────
# 4. ENVIRONMENTS  (lightweight, cartoon-style)
# ─────────────────────────────────────────────
def make_material(name, color, roughness=0.8, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value   = (*color, 1)
        bsdf.inputs["Roughness"].default_value    = roughness
        if emission > 0:
            bsdf.inputs["Emission Strength"].default_value = emission
            bsdf.inputs["Emission Color"].default_value    = (*color, 1)
    return mat

def add_mesh(primitive, name, location, scale=(1,1,1), mat=None, **kwargs):
    getattr(bpy.ops.mesh, f"primitive_{primitive}_add")(location=location, **kwargs)
    obj = bpy.context.object
    obj.name  = f"Env_{name}"
    obj.scale = scale
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj

log(f"Building '{ENV_CHOICE}' environment...")

if ENV_CHOICE == "park":
    # Grass ground
    add_mesh("plane", "Ground", (0,0,0), scale=(12,12,1),
             mat=make_material("Grass", (0.15, 0.55, 0.15)))
    # Tree trunk
    add_mesh("cylinder", "TreeTrunk", (-3, 3, 1.5), scale=(0.4, 0.4, 1.5),
             mat=make_material("Bark", (0.35, 0.2, 0.08)))
    # Tree top
    add_mesh("ico_sphere", "TreeTop", (-3, 3, 3.5), scale=(1.8, 1.8, 1.5),
             mat=make_material("Leaves", (0.1, 0.45, 0.1)))
    # Bench seat
    add_mesh("cube", "Bench", (2, 2, 0.4), scale=(1.2, 0.3, 0.1),
             mat=make_material("BenchWood", (0.55, 0.35, 0.15)))
    # Sky backdrop
    add_mesh("plane", "SkyBackdrop", (0, 6, 4), scale=(12, 0.1, 5),
             mat=make_material("Sky", (0.5, 0.75, 1.0), roughness=1.0))

elif ENV_CHOICE == "room":
    # Floor
    add_mesh("plane", "Floor", (0, 0, 0), scale=(8, 8, 1),
             mat=make_material("WoodFloor", (0.6, 0.4, 0.25), roughness=0.6))
    # Back wall
    add_mesh("plane", "WallBack", (0, 4, 3), scale=(8, 0.1, 4),
             mat=make_material("Wall", (0.9, 0.88, 0.82)))
    # Side wall
    add_mesh("plane", "WallLeft", (-4, 0, 3), scale=(0.1, 8, 4),
             mat=make_material("Wall2", (0.88, 0.88, 0.86)))
    # Sofa
    add_mesh("cube", "SofaSeat", (2.5, 2, 0.4), scale=(1.5, 0.7, 0.4),
             mat=make_material("Sofa", (0.2, 0.35, 0.55)))
    add_mesh("cube", "SofaBack", (2.5, 2.7, 0.9), scale=(1.5, 0.2, 0.6),
             mat=make_material("Sofa2", (0.2, 0.35, 0.55)))
    # Picture frame on wall
    add_mesh("plane", "Picture", (0, 3.9, 2.5), scale=(0.8, 0.05, 0.6),
             mat=make_material("Frame", (0.8, 0.6, 0.2)))

else:  # street
    # Road
    add_mesh("plane", "Road", (0, 0, 0), scale=(12, 12, 1),
             mat=make_material("Asphalt", (0.15, 0.15, 0.18), roughness=0.95))
    # Centre line
    add_mesh("plane", "RoadLine", (0, 0, 0.01), scale=(0.15, 5, 1),
             mat=make_material("RoadMark", (0.9, 0.85, 0.1)))
    # Building L
    add_mesh("cube", "BuildingL", (-5, 4, 3), scale=(2, 1, 3),
             mat=make_material("BuildingL", (0.45, 0.5, 0.6)))
    # Building R
    add_mesh("cube", "BuildingR", (5, 4, 4), scale=(2.5, 1.2, 4),
             mat=make_material("BuildingR", (0.55, 0.4, 0.4)))
    # Street lamp
    add_mesh("cylinder", "LampPost", (3, 1, 1.5), scale=(0.07, 0.07, 1.5),
             mat=make_material("Post", (0.2, 0.2, 0.25)))
    add_mesh("uv_sphere", "LampGlobe", (3, 1, 3.1), scale=(0.25, 0.25, 0.25),
             mat=make_material("LampGlow", (1.0, 0.95, 0.7), emission=4.0))

# ─────────────────────────────────────────────
# 5. CAMERA  (vertical 9:16, with animated movements)
# ─────────────────────────────────────────────
log("Adding animated camera...")
bpy.ops.object.camera_add(location=(0, -5, 1.8), rotation=(math.radians(90), 0, 0))
camera     = bpy.context.object
scene.camera = camera
camera.data.lens = 35     # Wide-ish for vertical Shorts
# DoF API changed across Blender versions — wrap safely
try:
    camera.data.dof.use_dof = True
    camera.data.dof.aperture_fstop = 3.5
except AttributeError:
    try:
        camera.data.use_dof = True
        camera.data.dof.aperture_fstop = 3.5
    except AttributeError:
        pass  # DoF not available in this build

# Scene split: divide total frames into 3 acts
act = TOTAL_FRAMES // 3

CAMERA_MOVES = [
    # (start, end, start_loc, end_loc)
    (1,          act,           (0, -5,  1.8),  (0, -4,  1.8)),   # Slow push-in
    (act,        act * 2,       (0, -4,  1.8),  (-1, -4.5, 1.8)), # Pan left
    (act * 2,    TOTAL_FRAMES,  (-1, -4.5, 1.8),(0, -3.5, 1.9)),  # Close-up rise
]
for (f_start, f_end, loc_start, loc_end) in CAMERA_MOVES:
    camera.location = loc_start
    camera.keyframe_insert("location", frame=f_start)
    camera.location = loc_end
    camera.keyframe_insert("location", frame=f_end)

# Smooth interpolation — safely wrapped for Blender 5.0
try:
    if camera.animation_data and camera.animation_data.action:
        for fc in camera.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
except (AttributeError, RuntimeError):
    pass  # Not critical if interpolation can't be set

# ─────────────────────────────────────────────
# 6. LIGHTING  (3-point cartoon rig)
# ─────────────────────────────────────────────
log("Adding 3-point lights...")
def add_area_light(name, location, rotation_deg, energy, size=2.0, color=(1,1,1)):
    bpy.ops.object.light_add(
        type='AREA',
        location=location,
        rotation=[math.radians(r) for r in rotation_deg]
    )
    lt = bpy.context.object
    lt.name             = name
    lt.data.energy      = energy
    lt.data.size        = size
    lt.data.color       = color
    return lt

add_area_light("KeyLight",  ( 2.5, -3,  3),   (45, 0,  45),  2000, size=2.0, color=(1.0, 0.97, 0.92))
add_area_light("FillLight", (-2.5, -2,  2.5),  (45, 0, -45),  800,  size=3.0, color=(0.8, 0.88, 1.0))
add_area_light("RimLight",  ( 0,    3,  3),    (135, 0,  0),  3000, size=1.5, color=(1.0, 0.95, 0.85))

# ─────────────────────────────────────────────
# 7. CHARACTER  (detect armature + mesh from loaded .blend)
# ─────────────────────────────────────────────
log("Detecting character rig...")
armature       = None
character_mesh = None

for obj in scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    if obj.type == 'MESH' and obj.data.shape_keys:
        character_mesh = obj

if armature:
    armature.location = (0, 0, 0)
    log(f"Found armature: {armature.name}")
else:
    log("WARNING: No armature found. Character animations will be skipped.")

if character_mesh:
    log(f"Found character mesh with shape keys: {character_mesh.name}")
else:
    log("WARNING: No mesh with shape keys found. Lip-sync will be skipped.")

# ─────────────────────────────────────────────
# 8. BODY ANIMATION  (NLA strips: walk → idle → sit)
# ─────────────────────────────────────────────
SCENE_ACTIONS = [
    ("Walk",   1,         act),
    ("Talk",   act,       act * 2),  # Use Talk/Idle while speaking
    ("Sit",    act * 2,   TOTAL_FRAMES),
]

if armature and armature.animation_data:
    log("Applying body animations via NLA...")

    if not armature.animation_data.nla_tracks:
        armature.animation_data.nla_tracks.new()

    track = armature.animation_data.nla_tracks[0]
    # Clear stale strips
    for s in list(track.strips):
        track.strips.remove(s)

    for (action_hint, f_start, f_end) in SCENE_ACTIONS:
        # Find best matching action
        best = None
        for act_data in bpy.data.actions:
            if action_hint.lower() in act_data.name.lower():
                best = act_data
                break

        if best:
            strip = track.strips.new(name=action_hint, start=int(f_start), action=best)
            duration = f_end - f_start
            act_len  = strip.action_frame_end - strip.action_frame_start
            if act_len > 0:
                strip.repeat          = max(1, duration / act_len)
            strip.blend_type      = 'REPLACE'
            strip.extrapolation   = 'HOLD_FORWARD'
            log(f"  • {action_hint} [{f_start}–{f_end}] using action '{best.name}'")
        else:
            log(f"  ⚠ No action found matching '{action_hint}' — skipping strip.")

# ─────────────────────────────────────────────
# 9. SHAPE-KEY HELPERS
# ─────────────────────────────────────────────
def find_shape_key(keyword):
    if not character_mesh or not character_mesh.data.shape_keys:
        return None
    for kb in character_mesh.data.shape_keys.key_blocks:
        if keyword.lower() in kb.name.lower():
            return kb
    return None

def set_keyframe(kb, value, frame, interp='BEZIER'):
    if kb is None:
        return
    kb.value = value
    kb.keyframe_insert(data_path="value", frame=frame)
    try:
        sk_anim = character_mesh.data.shape_keys.animation_data
        if sk_anim and sk_anim.action:
            for fc in sk_anim.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = interp
    except (AttributeError, RuntimeError):
        pass

# ─────────────────────────────────────────────
# 10. LIP-SYNC (Procedural Phonemes) & HEAD ANIM
# ─────────────────────────────────────────────
phonemes = {
    'A': find_shape_key("A") or find_shape_key("jaw") or find_shape_key("mouth_open"),
    'E': find_shape_key("E"),
    'O': find_shape_key("O"),
    'U': find_shape_key("U"),
    'M': find_shape_key("M") or find_shape_key("mouth_close")
}
valid_phonemes = {k: v for k, v in phonemes.items() if v is not None}
blink_key = find_shape_key("Blink") or find_shape_key("blink") or find_shape_key("eye_close")

head_bone = None
if armature:
    for b in armature.pose.bones:
        if "head" in b.name.lower() or "neck" in b.name.lower():
            head_bone = b
            break
if head_bone:
    log(f"Found head/neck bone: '{head_bone.name}' for procedural talking movements.")

if VOICE_FILE and os.path.exists(VOICE_FILE):
    log(f"Adding audio strip: {VOICE_FILE}")

    if not scene.sequence_editor:
        scene.sequence_editor_create()

    # Clear old strips
    for strip in list(scene.sequence_editor.sequences_all):
        scene.sequence_editor.sequences.remove(strip)

    audio_strip = scene.sequence_editor.sequences.new_sound(
        name="Voiceover",
        filepath=os.path.abspath(VOICE_FILE),
        channel=1,
        frame_start=1
    )
    # Adapt total length to audio if audio is shorter
    audio_frames = int(audio_strip.frame_duration)
    scene.frame_end = min(TOTAL_FRAMES, audio_frames)
    log(f"Audio duration: {audio_frames} frames — rendering {scene.frame_end} frames.")

    # Bake Audio Amplitude into a Custom Property on the Scene to drive Shape Keys
    log("Baking audio amplitude for procedural phonemes...")
    if valid_phonemes:
        scene["audio_amp"] = 0.0
        scene.keyframe_insert(data_path='["audio_amp"]', frame=1)
        
        try:
            bpy.context.area_type = "GRAPH_EDITOR" if hasattr(bpy.context, "area_type") else None
            bpy.ops.graph.sound_bake(filepath=os.path.abspath(VOICE_FILE), low=80.0, high=8000.0)
            
            if scene.animation_data and scene.animation_data.action:
                fc = next((f for f in scene.animation_data.action.fcurves if f.data_path == '["audio_amp"]'), None)
                if fc:
                    for kp in fc.keyframe_points:
                        f = int(kp.co[0])
                        amp = kp.co[1]
                        
                        if f > scene.frame_end:
                            break
                            
                        # Sample every 3 frames for distinct mouth syllables (avoid jitter)
                        if f % 3 == 0:
                            # 1. Reset all mouths
                            for k in valid_phonemes.keys():
                                set_keyframe(valid_phonemes[k], 0.0, f)
                            
                            # 2. Assign Phoneme & Head movement
                            if amp > 0.05:
                                # Speaking
                                phon_choice = random.choice([k for k in valid_phonemes.keys() if k != 'M'])
                                if not phon_choice: phon_choice = list(valid_phonemes.keys())[0]
                                set_keyframe(valid_phonemes[phon_choice], min(1.0, amp * 5.0), f)
                                
                                # Animate Head
                                if head_bone and random.random() > 0.5:
                                    head_bone.rotation_mode = 'XYZ'
                                    head_bone.rotation_euler = (
                                        random.uniform(-0.15, 0.15),
                                        random.uniform(-0.1, 0.1),
                                        random.uniform(-0.15, 0.15)
                                    )
                                    head_bone.keyframe_insert(data_path="rotation_euler", frame=f)
                            else:
                                # Silent -> Default to 'M' (closed mouth)
                                if 'M' in valid_phonemes:
                                    set_keyframe(valid_phonemes['M'], 1.0, f)
                                    
            log("Procedural phoneme Lip-sync and head movement bake complete.")
        except Exception as e:
            log(f"Procedural Lip Sync error: {e}")
    else:
        log("No phoneme shape keys found (A,E,O,U,M) — skipping lip-sync.")
else:
    log("No SHORTS_AUDIO provided — skipping lip-sync and audio strip.")

# ─────────────────────────────────────────────
# 11. PROCEDURAL BLINKING
# ─────────────────────────────────────────────
if blink_key:
    log("Baking procedural blinks...")
    f = 1
    while f < scene.frame_end:
        set_keyframe(blink_key, 0.0, f)
        f += random.randint(50, 120)   # Random gap between blinks
        if f >= scene.frame_end:
            break
        set_keyframe(blink_key, 1.0, f)       # Close eye
        set_keyframe(blink_key, 0.0, f + 3)   # Open eye
        f += 4
else:
    log("No blink shape key found — skipping blinking.")

# ─────────────────────────────────────────────
# 12. TITLE CARD  (simple text object, 0–2s)
# ─────────────────────────────────────────────
log(f"Adding title card: '{TOPIC_TITLE}'")
bpy.ops.object.text_add(location=(0, -4.5, 2.8))
title_obj = bpy.context.object
title_obj.name = "TitleCard"
title_obj.data.body         = TOPIC_TITLE.upper()
title_obj.data.align_x      = 'CENTER'
title_obj.data.size         = 0.22
title_obj.data.extrude      = 0.005
title_obj.rotation_euler[0] = math.radians(90)

title_mat = bpy.data.materials.new("TitleMat")
title_mat.use_nodes = True
bsdf_t = title_mat.node_tree.nodes.get("Principled BSDF")
if bsdf_t:
    bsdf_t.inputs["Base Color"].default_value      = (1.0, 0.85, 0.0, 1)
    bsdf_t.inputs["Emission Color"].default_value  = (1.0, 0.85, 0.0, 1)
    bsdf_t.inputs["Emission Strength"].default_value = 1.5
title_obj.data.materials.append(title_mat)

# Fade title in (frame 1) and out (frame 60 = 2s)
title_obj.hide_render = True
title_obj.keyframe_insert("hide_render", frame=1)
title_obj.hide_render = False
title_obj.keyframe_insert("hide_render", frame=2)
title_obj.hide_render = False
title_obj.keyframe_insert("hide_render", frame=59)
title_obj.hide_render = True
title_obj.keyframe_insert("hide_render", frame=60)

# ─────────────────────────────────────────────
# 13. SUBSCRIBE CTA  (last 3 seconds)
# ─────────────────────────────────────────────
cta_start = scene.frame_end - (FPS * 3)
log("Adding CTA overlay...")
bpy.ops.object.text_add(location=(0, -4.5, 0.6))
cta_obj = bpy.context.object
cta_obj.name              = "CTACard"
cta_obj.data.body         = "SUBSCRIBE FOR MORE"
cta_obj.data.align_x      = 'CENTER'
cta_obj.data.size         = 0.16
cta_obj.rotation_euler[0] = math.radians(90)

cta_mat = bpy.data.materials.new("CTAMat")
cta_mat.use_nodes = True
bsdf_c = cta_mat.node_tree.nodes.get("Principled BSDF")
if bsdf_c:
    bsdf_c.inputs["Base Color"].default_value      = (1, 1, 1, 1)
    bsdf_c.inputs["Emission Color"].default_value  = (1, 0.1, 0.1, 1)
    bsdf_c.inputs["Emission Strength"].default_value = 2.5
cta_obj.data.materials.append(cta_mat)

cta_obj.hide_render = True
cta_obj.keyframe_insert("hide_render", frame=1)
cta_obj.hide_render = False
cta_obj.keyframe_insert("hide_render", frame=cta_start)

# ─────────────────────────────────────────────
# 14. RENDER
# ─────────────────────────────────────────────
log(f"Starting native Blender render → {OUTPUT_PATH}")
log(f"  Resolution : 1080 x 1920")
log(f"  Frames     : {scene.frame_start} – {scene.frame_end}")
log(f"  Renderer   : {scene.render.engine}")
log(f"  Format     : {scene.render.image_settings.file_format}")

try:
    bpy.ops.render.render(animation=True)
    log(f"✅ Render complete! Video successfully created natively: {OUTPUT_PATH}")
except Exception as e:
    log(f"❌ Render failed: {e}")
    traceback.print_exc()
    sys.exit(1)
