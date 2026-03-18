import subprocess
import os
import json

def generate_lipsync(audio_file="outputs/audio.wav", output_file="outputs/lipsync.json"):
    """
    Generates lip-sync data using Rhubarb Lip Sync.
    Outputs a JSON file with mouth shapes and timestamps.
    """
    if not os.path.exists(audio_file):
        print(f"Audio file not found: {audio_file}")
        return False
        
    try:
        # 🛠️ DYNAMIC TOOL PATH (Windows local vs Render Linux)
        RHUBARB_PATH = os.environ.get("RHUBARB_PATH", r"C:\Users\User\Downloads\Rhubarb-Lip-Sync-1.14.0-Windows\Rhubarb-Lip-Sync-1.14.0-Windows\rhubarb.exe")
        if not os.path.exists(RHUBARB_PATH):
            RHUBARB_PATH = "rhubarb" # Fallback to PATH (e.g. on Linux/Render)
            
        process = subprocess.run(
            [RHUBARB_PATH, '-f', 'json', '-o', output_file, audio_file],
            capture_output=True,
            text=True,
            check=True
        )

        # RHUBARB MAPPING FOR CHARACTER_V2.BLEND
        mapping = {
            'A': 'MBP',
            'B': 'O',
            'C': 'AI', # Mapping AA to AI
            'D': 'E',
            'E': 'U',
            'F': 'FV',
            'G': 'mouth_open', # Proxy for TH
            'H': 'mouth_open', # Proxy for L
            'X': 'neutral'
        }

        if process.returncode == 0:
            # Post-process the JSON to include these explicit mappings
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            for cue in data.get("mouthCues", []):
                cue["shape_key"] = mapping.get(cue["value"], "neutral")
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"✅ Lip-sync data generated with mappings: {output_file}")
            return True
        else:
            print(f"Rhubarb error: {process.stderr}")
            return False
    except Exception as e:
        print(f"Error running Rhubarb: {e}")
        return False

if __name__ == "__main__":
    generate_lipsync()
