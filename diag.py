import requests
import json
import sys

def check():
    log = []
    log.append("Checking Ollama...")
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        log.append(f"Status: {r.status_code}")
        log.append(f"Response: {r.text[:200]}")
    except Exception as e:
        log.append(f"Ollama Error: {e}")

    log.append("\nChecking ComfyUI...")
    try:
        r = requests.get('http://localhost:8188/api/prompt', timeout=5)
        log.append(f"Status: {r.status_code}")
        log.append(f"Response: {r.text[:200]}")
    except Exception as e:
        log.append(f"ComfyUI Error: {e}")

    with open('diag_results.txt', 'w') as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    check()
