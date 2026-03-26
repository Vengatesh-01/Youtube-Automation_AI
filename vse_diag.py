import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")

def diag_vse():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    scene = bpy.context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    
    with open("vse_diag.txt", "w") as f:
        f.write(f"Sequence Editor Object: {scene.sequence_editor}\n")
        f.write(f"Attributes: {dir(scene.sequence_editor)}\n")
        
        # Check sequences_all vs sequences
        try:
            f.write(f"sequences count: {len(scene.sequence_editor.sequences)}\n")
        except Exception as e:
            f.write(f"sequences error: {e}\n")
            
        try:
            f.write(f"sequences_all count: {len(scene.sequence_editor.sequences_all)}\n")
        except Exception as e:
            f.write(f"sequences_all error: {e}\n")

if __name__ == "__main__":
    diag_vse()
