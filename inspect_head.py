import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")

def inspect_head():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    mesh = bpy.data.objects.get("CharacterMesh")
    if not mesh: return
    
    vgroup = mesh.vertex_groups.get("Head")
    if not vgroup: return
    
    min_co = [float('inf')] * 3
    max_co = [float('-inf')] * 3
    
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group == vgroup.index and g.weight > 0.5:
                # World space
                co = mesh.matrix_world @ v.co
                for i in range(3):
                    min_co[i] = min(min_co[i], co[i])
                    max_co[i] = max(max_co[i], co[i])
    
    print(f"HEAD_MIN: {min_co}")
    print(f"HEAD_MAX: {max_co}")

if __name__ == "__main__":
    inspect_head()
