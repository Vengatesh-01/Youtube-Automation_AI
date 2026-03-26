import os, subprocess, sys

SADTALKER_DIR = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main"
SADTALKER_PYTHON = os.path.join(SADTALKER_DIR, r"venv\Scripts\python.exe")
SADTALKER_INFERENCE = os.path.join(SADTALKER_DIR, "inference.py")

print("=== SADTALKER DIAGNOSTIC ===")
print(f"SadTalker dir exists: {os.path.isdir(SADTALKER_DIR)}")
print(f"inference.py exists:  {os.path.isfile(SADTALKER_INFERENCE)}")
print(f"venv python exists:   {os.path.isfile(SADTALKER_PYTHON)}")

print("\n=== INPUTS ===")
for f in ["inputs/portrait.png", "inputs/voice.wav", "inputs/script.txt"]:
    exists = os.path.isfile(f)
    size = os.path.getsize(f) if exists else 0
    print(f"  {f}: exists={exists}, size={size} bytes")

print("\n=== COMFYUI ===")
try:
    import requests
    r = requests.get("http://127.0.0.1:8188/system_stats", timeout=3)
    print(f"  ComfyUI running: True, response={r.status_code}")
except Exception as e:
    print(f"  ComfyUI running: False ({e})")

print("\n=== RESULTS DIR ===")
results = "./results"
if os.path.isdir(results):
    files = os.listdir(results)
    print(f"  Files in results: {files}")
else:
    print("  results/ dir does not exist")
