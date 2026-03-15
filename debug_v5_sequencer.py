import bpy
import sys
import os

def log(msg):
    print(f"[DEBUG] {msg}")

scene = bpy.context.scene
if not scene.sequence_editor:
    scene.sequence_editor_create()

log(f"SequenceEditor: {scene.sequence_editor}")

# Exhaustive scan of dir()
log("--- dir(scene.sequence_editor) ---")
for attr in dir(scene.sequence_editor):
    try:
        val = getattr(scene.sequence_editor, attr)
        log(f"  {attr}: {type(val)}")
        if attr == "sequences" or attr == "sequences_all":
            log(f"!!! FOUND {attr} !!!")
    except Exception as e:
        log(f"  {attr}: (error accessing)")

log("--- RNA Scan ---")
if hasattr(scene.sequence_editor, "bl_rna"):
    for prop in scene.sequence_editor.bl_rna.properties:
        log(f"  RNA Prop: {prop.identifier} (type: {prop.type})")

log("--- context sequences ---")
log(f"dir(bpy.context): {dir(bpy.context)}")
for attr in dir(bpy.context):
    if "sequen" in attr.lower():
        log(f"  Context Sequence Attr: {attr}")

sys.exit(0)
