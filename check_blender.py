import bpy
import sys

print("--- BLENDER ENVIRONMENT CHECK ---")
print(f"Blender Version: {bpy.app.version_string}")

# 1. Check Render Engines
engines = [e.identifier for e in bpy.types.RenderEngine.__subclasses__() if hasattr(e, 'identifier')]
print(f"RENDER_ENGINES: {engines}")

# 2. Check File Formats
formats = bpy.context.scene.render.image_settings.bl_rna.properties['file_format'].enum_items.keys()
print(f"FILE_FORMATS: {list(formats)}")

# 3. Check for specific audio features
print(f"Has sound_bake: {hasattr(bpy.ops.graph, 'sound_bake')}")

sys.exit(0)
