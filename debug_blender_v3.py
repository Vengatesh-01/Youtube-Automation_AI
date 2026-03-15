import bpy
import sys
import os

log_file = os.path.abspath("blender_debug.log")

with open(log_file, "w") as f:
    f.write("--- BLENDER 5.0 DIAGNOSTICS ---\n")
    try:
        scene = bpy.context.scene
        scene.render.image_settings.file_format = 'FFMPEG'
        ffmpeg = scene.render.ffmpeg
        
        f.write("\nFFMPEG Properties:\n")
        for p_name in ['format', 'codec', 'audio_codec', 'constant_rate_factor']:
            prop = ffmpeg.bl_rna.properties[p_name]
            f.write(f"{p_name}: {prop.type}\n")
            if prop.type == 'ENUM':
                f.write(f"  Options: {list(prop.enum_items.keys())}\n")
        
        f.write("\nAttempting explicit assignments:\n")
        
        # Test 1: Format
        try:
            ffmpeg.format = 'MPEG4'
            f.write("[OK] format = 'MPEG4'\n")
        except Exception as e:
            f.write(f"[FAIL] format = 'MPEG4': {e}\n")
            
        # Test 2: Codec
        try:
            ffmpeg.codec = 'H264'
            f.write("[OK] codec = 'H264'\n")
        except Exception as e:
            f.write(f"[FAIL] codec = 'H264': {e}\n")
            
        # Test 3: Audio
        try:
            ffmpeg.audio_codec = 'AAC'
            f.write("[OK] audio_codec = 'AAC'\n")
        except Exception as e:
            f.write(f"[FAIL] audio_codec = 'AAC': {e}\n")
            
        # Test 4: CRF
        try:
            crf_prop = ffmpeg.bl_rna.properties['constant_rate_factor']
            if crf_prop.type == 'ENUM':
                ffmpeg.constant_rate_factor = 'HIGH'
                f.write("[OK] constant_rate_factor = 'HIGH'\n")
            else:
                ffmpeg.constant_rate_factor = 23
                f.write("[OK] constant_rate_factor = 23\n")
        except Exception as e:
            f.write(f"[FAIL] constant_rate_factor: {e}\n")

    except Exception as e:
        f.write(f"\nCRITICAL ERROR: {e}\n")

print(f"Diagnostics written to: {log_file}")
sys.exit(0)
