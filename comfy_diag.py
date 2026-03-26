import requests
import json
import os

COMFY_URL = "http://127.0.0.1:8188"

def log(msg):
    with open("comfy_diag.log", "a") as f:
        f.write(msg + "\n")

log("Starting ComfyUI Diagnosis...")

try:
    # 1. Check object_info
    log("Checking object_info for AnimateDiff nodes...")
    resp = requests.get(f"{COMFY_URL}/object_info", timeout=30)
    resp.raise_for_status()
    nodes = resp.json()
    
    required_nodes = ["ADE_ApplyAnimateDiffModelSimple", "VHS_VideoCombine", "CheckpointLoaderSimple"]
    for node in required_nodes:
        if node in nodes:
            log(f"[OK] Node found: {node}")
        else:
            log(f"[MISSING] Node NOT found: {node}")

    # 2. Check models (checkpoints)
    log("\nChecking available checkpoints...")
    resp = requests.get(f"{COMFY_URL}/models/checkpoints", timeout=10)
    if resp.status_code == 200:
        log(f"Checkpoints: {resp.json()}")
    else:
        # Fallback if models API is not available
        log("Models API not directly accessible, checking if CheckpointLoaderSimple lists them.")
        if "CheckpointLoaderSimple" in nodes:
            log(f"CheckpointLoaderSimple inputs: {nodes['CheckpointLoaderSimple']['input']['required']['ckpt_name']}")

except Exception as e:
    log(f"CRITICAL DIAG ERROR: {e}")
