import bpy
import os
import sys
import math
import random
import traceback

# ─────────────────────────────────────────────
# 0. CONFIGURATION
# ─────────────────────────────────────────────
VOICE_FILE  = os.environ.get("SHORTS_AUDIO",  "")
TOPIC_TITLE = os.environ.get("SHORTS_TOPIC",  "Never Give Up")
OUTPUT_PATH = os.environ.get("SHORTS_OUTPUT", "outputs/final_short.mp4")
VIDEO_SEGMENTS = os.environ.get("VIDEO_SEGMENTS", "").split(",") # Paths to ComfyUI segments

FPS          = 30
TEMPLATE_PATH = "assets/shorts_template.blend" # Reusable template

os.makedirs(os.path.dirname(OUTPUT_PATH) if os.path.dirname(OUTPUT_PATH) else "outputs", exist_ok=True)

def log(msg):
    print(f"[BLENDER_ASSEMBLY] {msg}", flush=True)

# ─────────────────────────────────────────────
# 1. LOAD TEMPLATE & SETUP
# ─────────────────────────────────────────────
# This script is designed to be run as: blender -b [TEMPLATE] -P blender_shorts_generator.py
log("Setting up assembly scene...")
scene = bpy.context.scene
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = FPS

# Setup Sequencer
if not scene.sequence_editor:
    scene.sequence_editor_create()
else:
    # Clear existing strips
    for s in list(scene.sequence_editor.sequences):
        scene.sequence_editor.sequences.remove(s)

# ─────────────────────────────────────────────
# 2. IMPORT SEGMENTS & AUDIO
# ─────────────────────────────────────────────
current_frame = 1

# Add Audio
if VOICE_FILE and os.path.exists(VOICE_FILE):
    log(f"Adding audio: {VOICE_FILE}")
    try:
        audio_strip = scene.sequence_editor.sequences.new_sound(
            name="Voiceover",
            filepath=os.path.abspath(VOICE_FILE),
            channel=1,
            frame_start=1
        )
        total_duration = audio_strip.frame_final_end
        scene.frame_end = total_duration
    except Exception as e:
        log(f"Audio error: {e}")

# Add Video Segments (from ComfyUI)
log(f"Assembling {len(VIDEO_SEGMENTS)} segments...")
for seg_path in VIDEO_SEGMENTS:
    if not seg_path or not os.path.exists(seg_path):
        log(f"Skipping missing segment: {seg_path}")
        continue
    
    try:
        vid_strip = scene.sequence_editor.sequences.new_movie(
            name=os.path.basename(seg_path),
            filepath=os.path.abspath(seg_path),
            channel=2,
            frame_start=current_frame
        )
        # Ensure it fits the vertical aspect
        vid_strip.transform.scale_x = 1.0
        vid_strip.transform.scale_y = 1.0
        current_frame = vid_strip.frame_final_end
        log(f"  + Added {seg_path} starts at {vid_strip.frame_start}")
    except Exception as e:
        log(f"Segment import error ({seg_path}): {e}")

# Update frame end if no audio
if not VOICE_FILE:
    scene.frame_end = current_frame

# ─────────────────────────────────────────────
# 3. OVERLAYS (Title & Captions)
# ─────────────────────────────────────────────
# We can add 3D overlays from the template here
for obj in bpy.data.objects:
    if "Title" in obj.name:
        obj.hide_render = False
        if hasattr(obj.data, "body"):
            obj.data.body = TOPIC_TITLE.upper()

# ─────────────────────────────────────────────
# 4. RENDER FINAL
# ─────────────────────────────────────────────
log("Configuring final output...")
# Fallback logic for local environment without FFMPEG
try:
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.audio_codec = 'AAC'
    log("Set format to FFMPEG (MP4)")
except:
    log("FFMPEG failed, falling back to AVI_JPEG")
    scene.render.image_settings.file_format = 'AVI_JPEG'

scene.render.filepath = os.path.abspath(OUTPUT_PATH)

log(f"🎬 Rendering final short to: {scene.render.filepath}")
try:
    bpy.ops.render.render(animation=True)
    log("✅ Rendering complete!")
except Exception as e:
    log(f"❌ Render failed: {e}")
    sys.exit(1)
