import bpy
import os

INPUT_BLEND = os.path.abspath("YouTube_Automation_Free/assets/master_character.blend")

def diag():
    bpy.ops.wm.open_mainfile(filepath=INPUT_BLEND)
    scene = bpy.context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    
    print("--- Sequencer Diag ---")
    print(f"SE type: {type(scene.sequence_editor)}")
    print(f"Attributes: {dir(scene.sequence_editor)}")
    
    if hasattr(scene.sequence_editor, "sequences"):
        print(f"Sequences length: {len(scene.sequence_editor.sequences)}")
    if hasattr(scene.sequence_editor, "sequences_all"):
        print(f"Sequences_all length: {len(scene.sequence_editor.sequences_all)}")

if __name__ == "__main__":
    diag()
