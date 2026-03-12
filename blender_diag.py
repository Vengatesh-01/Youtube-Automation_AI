import bpy
import sys
import os
import json

def log(msg):
    print(f"[DIAG] {msg}")
    sys.stdout.flush()

def run_diag():
    results = {
        "version": bpy.app.version_string,
        "background": bpy.app.background,
        "file": bpy.data.filepath,
        "objects": [],
        "armatures": [],
        "meshes": []
    }
    
    try:
        log("Forcing open assets/character.blend...")
        asset_path = os.path.abspath("assets/character.blend")
        if not os.path.exists(asset_path):
            log(f"ERROR: File not found at {asset_path}")
            results["error"] = "Asset not found"
        else:
            bpy.ops.wm.open_mainfile(filepath=asset_path)
            results["file"] = bpy.data.filepath
            
        results["objects"] = [o.name for o in bpy.data.objects]
        results["armatures"] = [o.name for o in bpy.data.objects if o.type == 'ARMATURE']
        results["actions"] = [a.name for a in bpy.data.actions]
        
        for m in [o for o in bpy.data.objects if o.type == 'MESH']:
            mesh_info = {"name": m.name, "shape_keys": []}
            if m.data.shape_keys:
                mesh_info["shape_keys"] = [k.name for k in m.data.shape_keys.key_blocks]
            results["meshes"].append(mesh_info)

        with open("diag_results.json", "w") as f:
            json.dump(results, f, indent=4)
        log("DIAG_RESULTS_WRITTEN")
        
    except Exception as e:
        log(f"DIAGNOSTIC_FAILED: {str(e)}")
        with open("diag_results.json", "w") as f:
            json.dump({"error": str(e)}, f, indent=4)

if __name__ == "__main__":
    run_diag()
