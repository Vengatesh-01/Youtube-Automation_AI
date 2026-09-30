"""
retry_upload.py — Re-uploads the last assembled video without re-generating it.
Run this when the pipeline succeeded but the upload step failed due to a
network error (e.g. "Unable to find server at youtube.googleapis.com").

Usage:
    python retry_upload.py
"""

import os
import json
import re
import sys
from upload_agent import upload_video
from utils import safe_print

VIDEO_FILE   = "outputs/video/final_video.mp4"
METADATA_FILE = "outputs/youtube/metadata.json"
THUMB_PATTERN = "inputs/thumb_day_6_thum.jpeg"  # auto-detected below

def find_latest_thumbnail():
    """Try to auto-detect the most recently modified thumbnail in inputs/."""
    inputs_dir = "inputs"
    thumbs = [f for f in os.listdir(inputs_dir) if f.startswith("thumb_")]
    if not thumbs:
        return None
    thumbs.sort(key=lambda f: os.path.getmtime(os.path.join(inputs_dir, f)), reverse=True)
    return os.path.join(inputs_dir, thumbs[0])

def main():
    if not os.path.isfile(VIDEO_FILE):
        safe_print(f"❌ Video file not found: {VIDEO_FILE}")
        sys.exit(1)

    if not os.path.isfile(METADATA_FILE):
        safe_print(f"❌ Metadata file not found: {METADATA_FILE}")
        sys.exit(1)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    title = metadata.get("title", "").strip()
    # Strip emojis and invalid chars (same logic as main.py)
    title = re.sub(r'[<>]', '', title)
    title = title.encode('ascii', 'ignore').decode('ascii').strip()
    title = title.strip(' |:-') or "English Practice Podcast"
    title = title[:100]

    desc  = metadata.get("description", "")
    tags  = metadata.get("tags", [])

    thumb = find_latest_thumbnail()
    safe_print(f"🎬 Retrying upload for: {VIDEO_FILE}")
    safe_print(f"📝 Title: {title}")
    safe_print(f"🖼️  Thumbnail: {thumb}")

    url = upload_video(
        video_file=VIDEO_FILE,
        title=title,
        description=desc,
        thumbnail_file=thumb,
        tags=tags,
        privacy="public",
    )

    if url:
        safe_print(f"✅ Upload successful! {url}")
        with open("last_upload_url.txt", "w", encoding="utf-8") as f:
            f.write(url)
    else:
        safe_print("❌ Upload failed again. Check your internet connection and token.json.")
        sys.exit(1)

if __name__ == "__main__":
    main()
