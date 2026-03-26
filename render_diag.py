import bpy
import os

def diag_render():
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'FFMPEG'
    ffmpeg = scene.render.ffmpeg
    
    with open("render_diag.txt", "w") as f:
        f.write(f"FFMpegSettings Attributes: {dir(ffmpeg)}\n")
        # Check enums for constant_rate_factor
        try:
            # We can sometimes get info via rna_type
            prop = ffmpeg.rna_type.properties.get("constant_rate_factor")
            if prop:
                f.write(f"CRF Enums: {[e.identifier for e in prop.enum_items]}\n")
        except Exception as e:
            f.write(f"CRF Error: {e}\n")

if __name__ == "__main__":
    diag_render()
