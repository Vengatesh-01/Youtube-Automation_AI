import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")

def verify_final():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    scene = bpy.context.scene
    
    print("--- Final Production Check ---")
    mesh = bpy.data.objects.get("CharacterMesh")
    if mesh and mesh.data.shape_keys:
        k = mesh.data.shape_keys.key_blocks.get("SK_A")
        if k and k.animation_data and k.animation_data.drivers:
            d = k.animation_data.drivers[0]
            print(f"SK_A Driver: {d.driver.expression}, Variable: {d.driver.variables[0].name}")
        else:
            print("SK_A Driver not found!")
            
    if scene.sequence_editor and scene.sequence_editor.strips:
        print("Sequencer Strips:", [s.name for s in scene.sequence_editor.strips])

if __name__ == "__main__":
    verify_final()
