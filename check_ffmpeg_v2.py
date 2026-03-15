import bpy
import sys

scene = bpy.context.scene
scene.render.image_settings.file_format = 'FFMPEG'
ffmpeg = scene.render.ffmpeg

print("--- FFMPEG PROPERTY CHECK ---")

def check_prop(name):
    if hasattr(ffmpeg, name):
        prop = ffmpeg.bl_rna.properties[name]
        print(f"\nProperty: {name}")
        print(f"  Type: {prop.type}")
        if prop.type == 'ENUM':
            print(f"  Options: {list(prop.enum_items.keys())}")
    else:
        print(f"\nProperty: {name} (NOT FOUND)")

props = ['format', 'codec', 'audio_codec', 'constant_rate_factor', 'ffmpeg_preset', 'video_bitrate', 'audio_bitrate']
for p in props:
    check_prop(p)

print("\n--- ATTEMPTING ASSIGNMENT ---")
try:
    ffmpeg.format = 'MPEG4'
    print("[OK] format = 'MPEG4'")
except Exception as e:
    print(f"[FAIL] format = 'MPEG4': {e}")

try:
    ffmpeg.codec = 'H264'
    print("[OK] codec = 'H264'")
except Exception as e:
    print(f"[FAIL] codec = 'H264': {e}")

try:
    ffmpeg.audio_codec = 'AAC'
    print("[OK] audio_codec = 'AAC'")
except Exception as e:
    print(f"[FAIL] audio_codec = 'AAC': {e}")

try:
    # Check if int or enum
    prop = ffmpeg.bl_rna.properties['constant_rate_factor']
    if prop.type == 'ENUM':
        ffmpeg.constant_rate_factor = 'HIGH'
        print("[OK] constant_rate_factor = 'HIGH' (ENUM)")
    else:
        ffmpeg.constant_rate_factor = 23
        print("[OK] constant_rate_factor = 23 (INT)")
except Exception as e:
    print(f"[FAIL] constant_rate_factor: {e}")

sys.exit(0)
