import requests
import json

COMFY_URL = "http://127.0.0.1:8190"

def get_history():
    try:
        req = requests.get(f"{COMFY_URL}/history")
        history = req.json()
        print(json.dumps(history, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_history()
