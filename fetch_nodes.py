import requests
import json
import os

COMFY_URL = "http://127.0.0.1:8190"

def save_node_list():
    try:
        response = requests.get(f"{COMFY_URL}/object_info", timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Save full info
            with open("comfy_node_info_full.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            nodes = sorted(data.keys())
            with open("comfy_node_list.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(nodes))
            print(f"Successfully saved {len(nodes)} nodes to comfy_node_list.txt and full info to comfy_node_info_full.json")
        else:
            print(f"Error: Server returned status code {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    save_node_list()
