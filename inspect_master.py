import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")

def diag():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    with open("master_diag.txt", "w") as f:
        f.write("--- Objects ---\n")
        for o in bpy.data.objects:
            f.write(f"Name: {o.name}, Type: {o.type}\n")
            if o.type == 'ARMATURE':
                f.write(f"  Armature Name: {o.name}\n")
                f.write(f"  Bones: {', '.join([b.name for b in o.data.bones])}\n")
            if o.type == 'MESH':
                f.write(f"  Shape Keys: {list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else 'None'}\n")
    
if __name__ == "__main__":
    diag()
