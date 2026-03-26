import os
import shutil
import subprocess

def check_tool(name, default_path=None):
    """Checks if a tool exists in PATH or at a specific location."""
    path = shutil.which(name)
    if not path and default_path and os.path.exists(default_path):
        path = default_path
    
    if path:
        print(f"✅ FOUND: {name} at {path}")
        return path
    else:
        print(f"❌ MISSING: {name}")
        return None

def get_env_config():
    config = {}
    config['blender'] = check_tool("blender", r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
    config['piper'] = check_tool("piper")
    config['rhubarb'] = check_tool("rhubarb")
    config['ffmpeg'] = check_tool("ffmpeg")
    
    # Check for ComfyUI (Ollama is usually a URL, but we can ping)
    import requests
    try:
        requests.get("http://127.0.0.1:8190", timeout=2) # Default ComfyUI Port for this system
        print("✅ FOUND: ComfyUI (Active)")
        config['comfy_active'] = True
    except:
        print("⚠️ WARNING: ComfyUI not detected on port 8190")
        config['comfy_active'] = False
        
    return config

if __name__ == "__main__":
    get_env_config()
