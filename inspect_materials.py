import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/outputs/model_with_rig.blend")

def inspect_materials():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh:
        # Try finding any mesh
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        if meshes: mesh = meshes[0]
    
    if mesh:
        print(f"Mesh: {mesh.name}")
        print("Material Slots:")
        for i, slot in enumerate(mesh.material_slots):
            print(f"  Slot {i}: {slot.name}")
    else:
        print("Error: No mesh found!")

if __name__ == "__main__":
    inspect_materials()
