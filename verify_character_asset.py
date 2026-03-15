import bpy
import sys

def log(msg):
    print(f"[CHECK] {msg}")

log("--- CHARACTER ASSET VERIFICATION ---")

# 1. Armature
armature = next((obj for obj in bpy.data.objects if obj.type == 'ARMATURE'), None)
if armature:
    log(f"OK: Armature '{armature.name}' found.")
    bones = [b.name for b in armature.pose.bones]
    log(f"Bones: {bones}")
else:
    log("FAIL: No Armature found.")

# 2. Mesh & Shape Keys
mesh_obj = next((obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.data.shape_keys), None)
if mesh_obj:
    log(f"OK: Mesh '{mesh_obj.name}' with shape keys found.")
    keys = [kb.name for kb in mesh_obj.data.shape_keys.key_blocks]
    log(f"Shape Keys: {keys}")
else:
    log("FAIL: No Mesh with shape keys found.")

# 3. Actions
actions = [act.name for act in bpy.data.actions]
log(f"Actions found: {actions}")
required_actions = ["Idle", "Walk", "Sit", "Talk"]
for ra in required_actions:
    if ra in actions or any(ra.lower() in a.lower() for a in actions):
        log(f"OK: Action '{ra}' found.")
    else:
        log(f"FAIL: Action '{ra}' NOT found.")

sys.exit(0)
