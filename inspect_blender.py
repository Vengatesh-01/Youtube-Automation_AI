import bpy
import os
import sys

def inspect_blend(filepath):
    print(f"\n--- Inspecting: {filepath} ---")
    if not os.path.exists(filepath):
        print("File not found.")
        return

    try:
        bpy.ops.wm.open_mainfile(filepath=filepath)
        print("Objects:")
        for obj in bpy.data.objects:
            print(f" - {obj.name} ({obj.type})")
            if obj.type == 'MESH' and obj.data.shape_keys:
                print("   Shape Keys:")
                for key in obj.data.shape_keys.key_blocks:
                    print(f"     - {key.name}")
            if obj.type == 'ARMATURE':
                print("   Bones:")
                for bone in obj.data.bones:
                    print(f"     - {bone.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    blends = [
        r"c:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\assets\character.blend",
        r"c:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\assets\automated_character.blend",
        r"c:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\assets\character_v2.blend"
    ]
    for b in blends:
        inspect_blend(b)
