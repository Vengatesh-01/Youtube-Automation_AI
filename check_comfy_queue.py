import requests
import json

COMFY_URL = "http://127.0.0.1:8190"

def get_queue():
    try:
        req = requests.get(f"{COMFY_URL}/queue")
        queue = req.json()
        print(json.dumps(queue, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_queue()
