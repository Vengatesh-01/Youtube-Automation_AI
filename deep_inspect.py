import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/outputs/model_with_rig.blend")

def deep_inspect():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    
    print("--- Objects ---")
    for obj in bpy.data.objects:
        print(f"Object: {obj.name} (Type: {obj.type})")
        if obj.type == 'MESH':
            print(f"  Materials: {[s.name for s in obj.material_slots]}")
            print(f"  Vertex Groups: {[g.name for g in obj.vertex_groups]}")

    print("\n--- All Materials in Data ---")
    for mat in bpy.data.materials:
        print(f"Material: {mat.name}")

if __name__ == "__main__":
    deep_inspect()
