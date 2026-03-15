"""
guilt_blender_scene.py  – v2  VIVID / EEVEE
============================================
Run via:
  blender -b assets/character.blend -P guilt_blender_scene.py

Env vars:
  SHORTS_AUDIO    = absolute path to voice WAV/MP3
  SHORTS_OUTPUT   = output mp4 path
  SHORTS_TOPIC    = title card text
  TOTAL_SEC       = duration in seconds (default 20)
"""

import bpy, os, sys, math, json, random, traceback

# ───────────────────────────────────────────────
# 0. CONFIG
# ───────────────────────────────────────────────
VOICE_FILE   = os.environ.get("SHORTS_AUDIO",  "")
OUTPUT_PATH  = os.environ.get("SHORTS_OUTPUT", "outputs/shorts.mp4")
TOPIC_TITLE  = os.environ.get("SHORTS_TOPIC",  "Overcoming Guilt")
TOTAL_SEC    = int(os.environ.get("TOTAL_SEC", "20"))

FPS          = 30
TOTAL_FRAMES = FPS * TOTAL_SEC

os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)

CAPTIONS = [
    "Feeling guilty? You are not alone.",
    "We all carry mistakes we wish we could undo.",
    "But guilt is not meant to imprison you.",
    "Forgiving yourself is the bravest thing you can do.",
    "Every person you admire has messed up too.",
    "They chose to learn, not to suffer.",
    "What if you let go today?",
    "You are more than your worst moment.",
    "Let go, forgive yourself, and move forward.",
]

def log(m): print(f"[GUILT v2] {m}", flush=True)

log(f"Scene: {TOTAL_SEC}s | {TOTAL_FRAMES} frames | output={OUTPUT_PATH}")

# ───────────────────────────────────────────────
# 1. RENDER SETTINGS  –  EEVEE (fast + colourful)
# ───────────────────────────────────────────────
scene = bpy.context.scene

engine_set = False
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'):
    try:
        scene.render.engine = eng
        log(f"Engine: {eng}")
        engine_set = True
        break
    except Exception:
        continue

# EEVEE speed-up
try:
    ee = scene.eevee
    for attr, val in [("taa_render_samples", 16),
                      ("use_bloom",  True),
                      ("use_ssr",    False),
                      ("use_gtao",   False)]:
        if hasattr(ee, attr):
            setattr(ee, attr, val)
except Exception:
    pass

# Cycles fallback minimal
if scene.render.engine == 'CYCLES':
    scene.cycles.samples     = 4
    scene.cycles.device      = 'CPU'
    scene.cycles.max_bounces = 2
    try:
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'NONE'
    except Exception:
        pass

scene.render.resolution_x          = 1080
scene.render.resolution_y          = 1920
scene.render.resolution_percentage = 50   # 540×960 — fast, still looks good on phone
scene.render.fps                    = FPS
scene.frame_start                   = 1
scene.frame_end                     = TOTAL_FRAMES
scene.render.filepath               = os.path.abspath(OUTPUT_PATH)
scene.render.film_transparent       = False

# Output container
for fmt in ('FFMPEG', 'AVI_JPEG'):
    try:
        scene.render.image_settings.file_format = fmt
        if fmt == 'FFMPEG':
            scene.render.ffmpeg.format               = 'MPEG4'
            scene.render.ffmpeg.codec                = 'H264'
            scene.render.ffmpeg.audio_codec          = 'AAC'
            scene.render.ffmpeg.constant_rate_factor = 'HIGH'
        log(f"Format: {fmt}")
        break
    except Exception:
        continue

# ───────────────────────────────────────────────
# 2. WORLD — vivid warm sky gradient
# ───────────────────────────────────────────────
log("Setting world sky…")
if not scene.world:
    scene.world = bpy.data.worlds.new("GuiltSky")
scene.world.use_nodes = True
nt    = scene.world.node_tree
nodes = nt.nodes
links = nt.links

# Clear existing nodes
for n in list(nodes):
    nodes.remove(n)

# Sky gradient: amber→blue via sky texture
output_n = nodes.new('ShaderNodeOutputWorld')
bg_n     = nodes.new('ShaderNodeBackground')

# Use a SkyTexture node for natural gradient
try:
    sky_n = nodes.new('ShaderNodeTexSky')
    sky_n.sky_type = 'PREETHAM'
    sky_n.turbidity = 2.5
    mix_n = nodes.new('ShaderNodeMixRGB')
    mix_n.blend_type = 'MIX'
    mix_n.inputs['Fac'].default_value = 0.4
    mix_n.inputs['Color1'].default_value = (0.95, 0.72, 0.40, 1.0)  # warm amber
    mix_n.inputs['Color2'].default_value = (0.38, 0.65, 1.00, 1.0)  # sky blue
    links.new(mix_n.outputs['Color'], bg_n.inputs['Color'])
    bg_n.inputs['Strength'].default_value = 1.2
except Exception:
    bg_n.inputs['Color'].default_value    = (0.50, 0.72, 1.00, 1.0)
    bg_n.inputs['Strength'].default_value = 1.2

links.new(bg_n.outputs['Background'], output_n.inputs['Surface'])

# ───────────────────────────────────────────────
# 3. CLEAR OLD SCENE OBJECTS
# ───────────────────────────────────────────────
log("Clearing cameras / lights / env objects…")
for obj in list(bpy.data.objects):
    if obj.type in {'CAMERA', 'LIGHT'} or \
       obj.name.startswith(('Env_', 'Cap_', 'Title', 'CTA')):
        bpy.data.objects.remove(obj, do_unlink=True)

# ───────────────────────────────────────────────
# 4. MATERIAL HELPER
# ───────────────────────────────────────────────
def make_mat(name, base, roughness=0.7, metallic=0.0, emission=0.0, emit_col=None):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes_m = m.node_tree.nodes
    bsdf = nodes_m.get("Principled BSDF")
    if not bsdf:
        bsdf = nodes_m.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value  = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value   = roughness
    bsdf.inputs["Metallic"].default_value    = metallic
    if emission > 0:
        ec = emit_col or base
        try:
            bsdf.inputs["Emission Color"].default_value    = (*ec, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission
        except Exception:
            pass
    return m

def add_prim(prim_fn, env_name, loc, scale=(1,1,1), mat=None, **kw):
    prim_fn(location=loc, **kw)
    obj = bpy.context.object
    obj.name  = f"Env_{env_name}"
    obj.scale = scale
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj

# ───────────────────────────────────────────────
# 5. PARK ENVIRONMENT  (vivid cartoon colours)
# ───────────────────────────────────────────────
log("Building vivid park environment…")

G = bpy.ops.mesh

# Lush green grass ground
add_prim(G.primitive_plane_add, "Ground", (0,0,0), scale=(20,20,1),
         mat=make_mat("Grass", (0.13, 0.60, 0.18), roughness=0.85))

# Bright sky-blue horizon backdrop (tall plane behind scene)
add_prim(G.primitive_plane_add, "SkyBG", (0, 10, 5), scale=(20,0.1,7),
         mat=make_mat("SkyBG", (0.40, 0.72, 1.00), roughness=1.0))

# Warm-tan footpath
add_prim(G.primitive_plane_add, "Path", (0, 0, 0.005), scale=(1.5, 10, 1),
         mat=make_mat("Path", (0.80, 0.70, 0.52), roughness=0.9))

# Tree 1 (large, behind character left)
add_prim(G.primitive_cylinder_add, "Trunk1", (-4, 4, 2), scale=(0.45,0.45,2),
         mat=make_mat("Bark", (0.42, 0.22, 0.08)))
add_prim(G.primitive_ico_sphere_add, "Canopy1", (-4, 4, 5), scale=(2.5,2.5,2),
         mat=make_mat("Leaves", (0.12, 0.55, 0.12)), subdivisions=2)

# Tree 2 (smaller, right)
add_prim(G.primitive_cylinder_add, "Trunk2", (5, 5, 1.5), scale=(0.35,0.35,1.5),
         mat=bpy.data.materials["Bark"])
add_prim(G.primitive_ico_sphere_add, "Canopy2", (5, 5, 3.8), scale=(1.8,1.8,1.5),
         mat=bpy.data.materials["Leaves"], subdivisions=2)

# Wooden park bench (character sits on it)
add_prim(G.primitive_cube_add, "BenchSeat", (2.2, 1.5, 0.42), scale=(1.3, 0.40, 0.12),
         mat=make_mat("BenchWood", (0.65, 0.40, 0.18), roughness=0.75))
add_prim(G.primitive_cube_add, "BenchBack", (2.2, 1.90, 0.80), scale=(1.3, 0.10, 0.55),
         mat=bpy.data.materials["BenchWood"])
# Bench legs
for lx in (-1.0, 1.0):
    add_prim(G.primitive_cube_add, f"BenchLeg{int(lx)}", (2.2+lx*1.15, 1.65, 0.22),
             scale=(0.08, 0.30, 0.35), mat=bpy.data.materials["BenchWood"])

# Small flower cluster (foreground colour pops)
for fi in range(4):
    fx = random.uniform(-3, -1)
    fy = random.uniform(-0.5, 1.5)
    fc = random.choice([(0.95,0.2,0.3),(0.95,0.75,0.1),(0.85,0.3,0.9),(0.2,0.7,0.95)])
    add_prim(G.primitive_uv_sphere_add, f"Flower{fi}", (fx, fy, 0.18),
             scale=(0.15,0.15,0.15), mat=make_mat(f"Flower{fi}", fc, roughness=0.6),
             segments=8, ring_count=6)
    add_prim(G.primitive_cylinder_add, f"Stem{fi}", (fx, fy, 0.09),
             scale=(0.03,0.03,0.12),
             mat=make_mat(f"Stem{fi}", (0.15,0.55,0.15)))

# ───────────────────────────────────────────────
# 6. CAMERA  — vertical 9:16, framing character
# ───────────────────────────────────────────────
log("Adding Shorts camera (9:16, character-framing)…")
bpy.ops.object.camera_add(location=(0.2, -4.5, 1.55),
                           rotation=(math.radians(88), 0, math.radians(2)))
camera = bpy.context.object
scene.camera = camera
camera.data.lens = 28          # slightly wider — shows character + environment
try:
    camera.data.dof.use_dof        = True
    camera.data.dof.aperture_fstop = 4.5   # gentle blur
except AttributeError:
    pass

# Smooth animated camera: gentle push-in + slight tilt
act3 = TOTAL_FRAMES // 3
MOVES = [
    (1,        act3,        (0.2, -4.5, 1.55), (0.1, -3.8, 1.60)),
    (act3,     act3*2,      (0.1, -3.8, 1.60), (-0.4,-4.0, 1.70)),
    (act3*2,   TOTAL_FRAMES,(-0.4,-4.0, 1.70), (0.0, -3.2, 1.85)),
]
for fs, fe, ls, le in MOVES:
    camera.location = ls
    camera.keyframe_insert("location", frame=fs)
    camera.location = le
    camera.keyframe_insert("location", frame=fe)

try:
    if camera.animation_data and camera.animation_data.action:
        for fc in camera.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
except Exception:
    pass

# ───────────────────────────────────────────────
# 7. LIGHTING  — warm 3-point + sun
# ───────────────────────────────────────────────
log("Adding warm 3-point lights…")

def add_light(name, loc, rot_deg, energy, ltype='AREA', size=2.0, color=(1,1,1)):
    bpy.ops.object.light_add(type=ltype, location=loc,
                              rotation=[math.radians(r) for r in rot_deg])
    lt = bpy.context.object
    lt.name        = name
    lt.data.energy = energy
    lt.data.color  = color
    if ltype == 'AREA':
        lt.data.size = size
    elif ltype == 'SUN':
        lt.data.angle = 0.05
    return lt

# Sun (warm morning light)
add_light("Sun",      (5, -8, 8),   (45, 0, 30),  3.0,  ltype='SUN',
          color=(1.0, 0.93, 0.80))
# Key light (warm)
add_light("KeyLight", (2.5, -3, 3), (50, 0, 45),  2500, size=2.0,
          color=(1.0, 0.92, 0.80))
# Fill light (cool blue — contrast)
add_light("Fill",     (-3, -2, 2.5),(45, 0,-45),  1000, size=3.5,
          color=(0.75, 0.85, 1.00))
# Rim light (back glow)
add_light("Rim",      (0,  4, 3),   (135, 0, 0),  4000, size=1.5,
          color=(1.0, 0.88, 0.65))

# ───────────────────────────────────────────────
# 8. CHARACTER DETECTION
# ───────────────────────────────────────────────
log("Detecting character rig…")
armature       = None
character_mesh = None
for obj in scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    if obj.type == 'MESH' and obj.data.shape_keys:
        character_mesh = obj

if armature:
    armature.location = (0, 0, 0)
    log(f"  Armature: {armature.name}")
else:
    log("  ⚠ No armature — animations skipped.")
if character_mesh:
    log(f"  Mesh+ShapeKeys: {character_mesh.name}")
else:
    log("  ⚠ No shape-key mesh — lip-sync skipped.")

# ───────────────────────────────────────────────
# 9. BODY ANIMATION (NLA)
# ───────────────────────────────────────────────
a = TOTAL_FRAMES // 3
ACTIONS = [("Idle", 1, a), ("Talk", a, a*2), ("Idle", a*2, TOTAL_FRAMES)]

if armature and armature.animation_data:
    log("Applying NLA body animations…")
    if not armature.animation_data.nla_tracks:
        armature.animation_data.nla_tracks.new()
    track = armature.animation_data.nla_tracks[0]
    for s in list(track.strips): track.strips.remove(s)

    for hint, fs, fe in ACTIONS:
        best = None
        for ad in bpy.data.actions:
            if hint.lower() in ad.name.lower():
                best = ad; break
        if best:
            strip = track.strips.new(name=hint, start=int(fs), action=best)
            dur = fe - fs
            al  = abs(strip.action_frame_end - strip.action_frame_start)
            if al > 0: strip.repeat = max(1.0, float(dur) / float(al))
            strip.blend_type    = 'REPLACE'
            strip.extrapolation = 'HOLD_FORWARD'
            log(f"  NLA {hint}[{fs}→{fe}] → {best.name}")
        else:
            log(f"  ⚠ No action '{hint}'")

# ───────────────────────────────────────────────
# 10. SHAPE KEY HELPERS
# ───────────────────────────────────────────────
def find_sk(kw):
    if not character_mesh or not character_mesh.data.shape_keys: return None
    for kb in character_mesh.data.shape_keys.key_blocks:
        if kw.lower() in kb.name.lower(): return kb
    return None

def sk_key(kb, val, frame):
    if kb is None: return
    kb.value = val
    kb.keyframe_insert(data_path="value", frame=frame)

phonemes = {k: find_sk(k) for k in ("A","E","O","U","M")}
valid_ph  = {k: v for k,v in phonemes.items() if v}
blink_sk  = find_sk("Blink") or find_sk("blink") or find_sk("eye_close")

# ───────────────────────────────────────────────
# 11. AUDIO STRIP
# ───────────────────────────────────────────────
if VOICE_FILE and os.path.exists(VOICE_FILE):
    log(f"Adding audio: {VOICE_FILE}")
    if scene.sequence_editor:
        try:
            for s in list(scene.sequence_editor.sequences):
                scene.sequence_editor.sequences.remove(s)
        except Exception:
            try: bpy.context.scene.sequence_editor_remove()
            except Exception: pass
    if not scene.sequence_editor:
        scene.sequence_editor_create()

    seqs = getattr(scene.sequence_editor, "sequences", None) \
        or getattr(scene.sequence_editor, "sequences_all", None)

    if seqs:
        try:
            astrip = seqs.new_sound("Voiceover", VOICE_FILE, channel=1, frame_start=1)
            af = int(astrip.frame_duration)
            scene.frame_end = min(TOTAL_FRAMES, af)
            log(f"  Audio OK — frame_end={scene.frame_end}")
        except Exception as e:
            log(f"  Audio error: {e}")
    else:
        try:
            bpy.ops.sequencer.sound_strip_add(filepath=VOICE_FILE, frame_start=1, channel=1)
        except Exception as e:
            log(f"  Audio operator error: {e}")
else:
    log("No audio file — skipping.")

# ───────────────────────────────────────────────
# 12. PROCEDURAL LIP-SYNC
# ───────────────────────────────────────────────
if valid_ph:
    ph_keys = [k for k in valid_ph if k != 'M']
    cap_dur = TOTAL_FRAMES // max(1, len(CAPTIONS))
    for ci in range(len(CAPTIONS)):
        cs = 1 + ci * cap_dur
        ce = cs + cap_dur
        sk_key(valid_ph.get('M'), 1.0, cs)
        for f in range(cs + 3, ce - 4, 3):
            for k in valid_ph: sk_key(valid_ph[k], 0.0, f)
            if ph_keys:
                pk = ph_keys[f % len(ph_keys)]
                sk_key(valid_ph[pk], 0.55 + random.random()*0.45, f)
        for k in valid_ph: sk_key(valid_ph[k], 0.0, ce - 2)
        if valid_ph.get('M'): sk_key(valid_ph['M'], 0.9, ce - 2)

# ───────────────────────────────────────────────
# 13. BLINKING
# ───────────────────────────────────────────────
if blink_sk:
    f = 1
    while f < scene.frame_end:
        sk_key(blink_sk, 0.0, f)
        f += random.randint(55, 130)
        if f >= scene.frame_end: break
        sk_key(blink_sk, 1.0, f)
        sk_key(blink_sk, 0.0, f + 3)
        f += 4

# ───────────────────────────────────────────────
# 14. TITLE CARD  (0–2.5 s, glowing gold)
# ───────────────────────────────────────────────
log(f"Title card: '{TOPIC_TITLE}'")
try:
    bpy.ops.object.text_add(location=(0, -4.3, 3.4))
    tc = bpy.context.object
    tc.name = "TitleCard"
    tc.data.body    = TOPIC_TITLE.upper()
    tc.data.align_x = 'CENTER'
    tc.data.size    = 0.22
    tc.data.extrude = 0.008
    tc.rotation_euler[0] = math.radians(90)
    tm = make_mat("TitleMat", (1.0, 0.87, 0.05), roughness=0.2,
                  emission=3.5, emit_col=(1.0, 0.87, 0.05))
    tc.data.materials.clear(); tc.data.materials.append(tm)
    tc.hide_render = True;  tc.keyframe_insert("hide_render", frame=1)
    tc.hide_render = False; tc.keyframe_insert("hide_render", frame=2)
    tc.hide_render = False; tc.keyframe_insert("hide_render", frame=72)
    tc.hide_render = True;  tc.keyframe_insert("hide_render", frame=73)
except Exception as e:
    log(f"Title card error: {e}")

# ───────────────────────────────────────────────
# 15. ANIMATED CAPTIONS  (white glow text)
# ───────────────────────────────────────────────
log(f"Baking {len(CAPTIONS)} captions…")
cap_dur = max(FPS * 2, TOTAL_FRAMES // max(1, len(CAPTIONS)))
cap_mat = make_mat("CapMat", (1.0,1.0,1.0), roughness=0.5,
                   emission=4.0, emit_col=(1.0,1.0,1.0))

for i, line in enumerate(CAPTIONS):
    try:
        cs = 1 + i * cap_dur
        ce = cs + cap_dur - 5
        display = line if len(line) <= 42 else line[:39] + "…"
        bpy.ops.object.text_add(location=(0, -4.3, 0.72))
        co = bpy.context.object
        co.name = f"Cap_{i:02d}"
        co.data.body    = display
        co.data.align_x = 'CENTER'
        co.data.size    = 0.14
        co.rotation_euler[0] = math.radians(90)
        co.data.materials.clear(); co.data.materials.append(cap_mat)

        co.hide_render = True;  co.keyframe_insert("hide_render", frame=max(1, cs-1))
        co.hide_render = False; co.keyframe_insert("hide_render", frame=cs)
        co.hide_render = False; co.keyframe_insert("hide_render", frame=ce)
        co.hide_render = True;  co.keyframe_insert("hide_render", frame=ce+1)
    except Exception as e:
        log(f"Caption {i} error: {e}")

# ───────────────────────────────────────────────
# 16. SUBSCRIBE CTA  (last 3 s)
# ───────────────────────────────────────────────
cta_start = max(1, scene.frame_end - FPS * 3)
try:
    bpy.ops.object.text_add(location=(0, -4.3, 0.38))
    cta = bpy.context.object
    cta.name = "CTACard"
    cta.data.body    = "SUBSCRIBE FOR MORE ❤"
    cta.data.align_x = 'CENTER'
    cta.data.size    = 0.14
    cta.rotation_euler[0] = math.radians(90)
    cta_m = make_mat("CTAMat", (1.0,0.15,0.15), roughness=0.4,
                     emission=3.0, emit_col=(1.0,0.15,0.15))
    cta.data.materials.clear(); cta.data.materials.append(cta_m)
    cta.hide_render = True;  cta.keyframe_insert("hide_render", frame=1)
    cta.hide_render = False; cta.keyframe_insert("hide_render", frame=cta_start)
except Exception as e:
    log(f"CTA error: {e}")

# ───────────────────────────────────────────────
# 17. RENDER
# ───────────────────────────────────────────────
log(f"Rendering {scene.frame_end} frames → {os.path.abspath(OUTPUT_PATH)}")
try:
    bpy.ops.render.render(animation=True)
    log(f"✅ Render complete!")
except Exception as e:
    log(f"❌ Render FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)
