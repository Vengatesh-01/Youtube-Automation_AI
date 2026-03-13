import bpy
try:
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG_VIDEO'
    print("SUCCESS: FFMPEG_VIDEO")
except Exception as e:
    print(f"ERROR: {e}")
