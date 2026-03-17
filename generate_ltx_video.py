"""
generate_ltx_video.py
---------------------
Triggers the LTX-Video ComfyUI workflow via HTTP API.
Polls for completion, downloads the resulting MP4, and saves it to ./outputs/.

Usage:
    python generate_ltx_video.py [optional: your prompt text here]

Default prompt is the cartoon ninja scene if none is provided.
"""

import requests
import json
import time
import os
import sys
import random
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
COMFY_URL      = "http://127.0.0.1:8190"
WORKFLOW_FILE  = os.path.join(os.path.dirname(__file__), "ltx_video_workflow.json")
OUTPUT_DIR     = os.path.join(os.path.dirname(__file__), "outputs")
POLL_INTERVAL  = 15   # seconds between history checks
TIMEOUT        = 3600  # 60 min max for CPU

DEFAULT_PROMPT = (
    "cartoon ninja character standing in a village, cinematic lighting, "
    "subtle movement, anime style, high detail"
)
NEGATIVE_PROMPT = (
    "low quality, blurry, static, distorted, watermark, text overlay"
)
# ───────────────────────────────────────────────────────────────────────────


def load_workflow(fpath: str) -> dict:
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


def queue_prompt(workflow: dict) -> dict | None:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(f"{COMFY_URL}/prompt", data=payload,
                             headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"[ERROR] Server returned {resp.status_code}: {resp.text}")
            return None
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Could not queue prompt: {e}")
        return None


def check_history(prompt_id: str) -> dict | None:
    try:
        resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] History check failed: {e}")
        return None


def download_output(filename: str, subfolder: str = "") -> str | None:
    """Download the generated video from ComfyUI and save locally."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    params = {"filename": filename, "type": "output"}
    if subfolder:
        params["subfolder"] = subfolder
    url = f"{COMFY_URL}/view"
    try:
        resp = requests.get(url, params=params, timeout=120)
        resp.raise_for_status()
        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "wb") as f:
            f.write(resp.content)
        print(f"[OK] Video saved → {os.path.abspath(out_path)}")
        return out_path
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None


def extract_output_file(history_entry: dict) -> tuple[str, str] | tuple[None, None]:
    """
    Return (filename, subfolder) from whichever output node has gifs/images.
    Searches all output nodes so the function is robust to node-ID changes.
    """
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        for key in ("gifs", "images", "videos"):
            if key in node_out and node_out[key]:
                item = node_out[key][0]
                filename  = item.get("filename", "")
                subfolder = item.get("subfolder", "")
                if filename:
                    print(f"[INFO] Output from node {node_id} → {filename}")
                    return filename, subfolder
    return None, None


def generate_video(
    positive_prompt: str = DEFAULT_PROMPT,
    negative_prompt: str = NEGATIVE_PROMPT,
    seed: int | None = None,
    steps: int = 20,
    cfg: float = 3.0,
    width: int = 512,
    height: int = 512,
    num_frames: int = 25,
    frame_rate: float = 24.0,
    filename_prefix: str = "LTX_Output",
) -> str | None:
    """
    Queue an LTX video generation job and wait for the output.

    Returns the local path to the saved MP4, or None on failure.
    """
    if not os.path.exists(WORKFLOW_FILE):
        print(f"[ERROR] Workflow file not found: {WORKFLOW_FILE}")
        return None

    workflow = load_workflow(WORKFLOW_FILE)

    # ── Patch prompts ──────────────────────────────────────────────────────
    workflow["5"]["inputs"]["text"] = positive_prompt   # Positive Prompt node
    workflow["6"]["inputs"]["text"] = negative_prompt   # Negative Prompt node

    # ── Patch KSampler params ──────────────────────────────────────────────
    workflow["9"]["inputs"]["seed"]   = seed if seed is not None else random.randint(0, 2**32 - 1)
    workflow["9"]["inputs"]["steps"]  = steps
    workflow["9"]["inputs"]["cfg"]    = cfg

    # ── Patch resolution / frames ──────────────────────────────────────────
    workflow["8"]["inputs"]["width"]   = width
    workflow["8"]["inputs"]["height"]  = height
    workflow["8"]["inputs"]["length"]  = num_frames

    # ── Patch LTXV frame-rate conditioning ────────────────────────────────
    workflow["7"]["inputs"]["frame_rate"] = frame_rate

    # ── Patch VHS output name & fps ───────────────────────────────────────
    workflow["11"]["inputs"]["filename_prefix"] = filename_prefix
    workflow["11"]["inputs"]["frame_rate"]      = int(frame_rate)

    print(f"\n{'='*60}")
    print(f"  Prompt   : {positive_prompt[:80]}...")
    print(f"  Size     : {width}x{height} @ {frame_rate}fps  ({num_frames} frames)")
    print(f"  Steps    : {steps}   CFG: {cfg}   Seed: {workflow['9']['inputs']['seed']}")
    print(f"  Sending to ComfyUI at {COMFY_URL} ...")
    print(f"{'='*60}\n")

    # Debug: write the workflow being sent to a file
    with open("debug_workflow_sent.json", "w", encoding="utf-8") as df:
        json.dump(workflow, df, indent=2)
    print("[DEBUG] Workflow sent written to debug_workflow_sent.json")

    response = queue_prompt(workflow)
    if not response or "prompt_id" not in response:
        print(f"[ERROR] Failed to queue. Server response: {response}")
        return None

    prompt_id = response["prompt_id"]
    print(f"[OK] Queued - Prompt ID: {prompt_id}")
    print(f"[INFO] Waiting for CPU generation (this can take 10-60+ minutes)...\n")

    # ── Poll for completion ────────────────────────────────────────────────
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        elapsed = int(time.time() - (deadline - TIMEOUT))
        print(f"[{elapsed:>5}s elapsed] Checking history ...", end="\r")

        history = check_history(prompt_id)
        if history and prompt_id in history:
            print(f"\n[OK] Generation complete after ~{elapsed}s")
            filename, subfolder = extract_output_file(history[prompt_id])
            if filename:
                return download_output(filename, subfolder)
            else:
                print("[WARN] Generation finished but no output file found in history.")
                return None

    print(f"\n[ERROR] Timed out after {TIMEOUT//60} minutes.")
    return None


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT
    result = generate_video(positive_prompt=user_prompt)
    if result:
        print(f"\n[SUCCESS] Video ready: {result}")
    else:
        print("\n[FAILED] Video generation failed. Check logs above.")
