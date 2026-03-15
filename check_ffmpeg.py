import bpy
import sys

scene = bpy.context.scene
scene.render.image_settings.file_format = 'FFMPEG'

print("--- FFMPEG ENUM VALUES ---")
print("FORMATS:", scene.render.ffmpeg.bl_rna.properties['format'].enum_items.keys())
print("CODECS:", scene.render.ffmpeg.bl_rna.properties['codec'].enum_items.keys())
print("AUDIO_CODECS:", scene.render.ffmpeg.bl_rna.properties['audio_codec'].enum_items.keys())

sys.exit(0)
