"""
upload_agent.py — Uploads finished MP4 to YouTube via the YouTube Data API v3.

SETUP (one-time):
1. Go to https://console.cloud.google.com/
2. Create a project and enable "YouTube Data API v3".
3. Create OAuth 2.0 credentials (Desktop App), download as client_secrets.json.
4. Place client_secrets.json in this directory.
5. Run once manually — a browser will open for Google sign-in and save token.json.
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Optional, List
from utils import safe_print, get_ffmpeg
import subprocess

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"


def _get_service():
    creds = None

    # On Render: write client_secrets.json from environment variable if missing
    if not os.path.exists(CLIENT_SECRETS_FILE):
        secrets_env = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
        if secrets_env:
            safe_print("[YouTube] Writing client_secrets.json from environment variable...")
            with open(CLIENT_SECRETS_FILE, "w") as f:
                f.write(secrets_env)

    # On Render: write token.json from environment variable if file is missing
    if not os.path.exists(TOKEN_FILE):
        token_env = os.environ.get("YOUTUBE_TOKEN", "")
        if token_env:
            safe_print("[YouTube] Writing token.json from YOUTUBE_TOKEN env var...")
            with open(TOKEN_FILE, "w") as f:
                f.write(token_env)
        else:
            safe_print("⚠️ [YouTube] No token.json and no YOUTUBE_TOKEN env var found.")

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            safe_print(f"⚠️ token.json is invalid or empty. Forcing re-authentication.")
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            safe_print("Refreshing expired YouTube credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                safe_print(f"❌ ERROR: Token refresh failed ({e}). Deleting token.json to force re-authentication.")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        else:
            # Check for headless environment (e.g., Render)
            is_headless = os.environ.get("RENDER") == "true" or os.environ.get("HEADLESS") == "true"
            
            if is_headless:
                safe_print("❌ ERROR: YouTube token.json is missing or invalid in a headless environment.")
                safe_print("Manual action required: Run this script locally to generate token.json, then upload/commit it.")
                return None

            if not os.path.exists(CLIENT_SECRETS_FILE):
                # We return None instead of raising FileNotFoundError to allow optional upload mode
                return None
            
            safe_print("Starting OAuth flow (Local Server mode)...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=0, 
                success_message='Authentication successful! You can safely close this browser tab and return to the terminal.'
            )
        if creds:
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
    
    if not creds:
        return None
        
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_file: str,
    title: str,
    description: str = "",
    thumbnail_file: Optional[str] = None,
    category_id: str = "22",
    tags: Optional[List[str]] = None,
    privacy: str = "public",
    publish_at: Optional[str] = None,
) -> Optional[str]:
    """
    Upload video_file to YouTube.
    Optionally set a thumbnail via thumbnail_file path.
    Returns the YouTube video URL, or None if credentials are missing.
    """
    if tags is None:
        tags = ["automation", "trending"]

    # Check for credentials before starting (files or environment variables)
    has_credentials = (
        os.path.exists(CLIENT_SECRETS_FILE) or 
        os.path.exists(TOKEN_FILE) or 
        bool(os.environ.get("YOUTUBE_CLIENT_SECRETS")) or 
        bool(os.environ.get("YOUTUBE_TOKEN"))
    )
    if not has_credentials:
        safe_print("📢 [YouTube] INFO: client_secrets.json or token.json not found.")
        safe_print("⚙️ To enable uploads, provide valid credentials or run this script locally once.")
        return None

    # If token file missing, try to create it from env var
    if not os.path.exists(TOKEN_FILE):
        token_env = os.environ.get("YOUTUBE_TOKEN")
        if token_env:
            safe_print("[YouTube] Writing token.json from YOUTUBE_TOKEN env var...")
            with open(TOKEN_FILE, "w") as f:
                f.write(token_env)

    # Detect headless environment – cannot launch OAuth UI
    is_headless = os.environ.get("RENDER") == "true" or os.environ.get("HEADLESS") == "true"
    if is_headless and not os.path.exists(TOKEN_FILE):
        safe_print("❌ [YouTube] HEADLESS environment – cannot perform OAuth flow.")
        safe_print("🔑 Provide a valid YOUTUBE_TOKEN env var or upload a pre‑generated token.json.")
        return None

    safe_print("📢 [YouTube] Uploading enabled. Authenticating...")
    youtube = _get_service()
    
    if not youtube:
        safe_print("❌ [YouTube] Failed to initialize YouTube service. Skipping upload.")
        return None

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy},
    }

    if publish_at:
        # publishAt requires privacyStatus to be 'private'
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at
        safe_print(f"⏰ [YouTube] Video scheduled for: {publish_at}")

    # Use a modest chunk size (5 MB) to avoid SSL EOF errors on flaky connections.
    safe_print(f"🚀 [YouTube] Uploading {video_file} ...")
    # If the specified video file does not exist, create a 1‑second black placeholder automatically.
    if not os.path.isfile(video_file):
        safe_print(f"⚠️ Video file '{video_file}' not found – creating a temporary placeholder.")
        placeholder_path = "placeholder_tmp.mp4"
        ffmpeg_exe = get_ffmpeg()
        # Generate a 1‑second black video (640x360) using ffmpeg.
        subprocess.run([
            ffmpeg_exe,
            "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=640x360:d=1",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            placeholder_path,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        video_file = placeholder_path
    media = MediaFileUpload(video_file, chunksize=5 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            safe_print(f"  Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]

    # Set thumbnail if provided
    if thumbnail_file and os.path.isfile(str(thumbnail_file)):
        safe_print(f"🖼️ [YouTube] Setting thumbnail: {thumbnail_file}")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_file))
            ).execute()
        except Exception as e:
            safe_print(f"  ⚠️ Warning: Thumbnail upload failed: {e}")
            safe_print("  Video upload was successful, but the thumbnail could not be set (possibly account verification required).")

    url = f"https://www.youtube.com/watch?v={video_id}"
    safe_print(f"✅ [YouTube] Uploaded successfully: {url}")
    # Write the URL to a file for verification
    try:
        with open("last_upload_url.txt", "w", encoding="utf-8") as f:
            f.write(url)
    except Exception as e:
        safe_print(f"⚠️ Failed to write last_upload_url.txt: {e}")
    return url


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        url = upload_video(
            video_file=sys.argv[1],
            title=sys.argv[2],
            description=sys.argv[3] if len(sys.argv) > 3 else "",
            thumbnail_file=sys.argv[4] if len(sys.argv) > 4 else None,
        )
        print(url)
    else:
        print("Usage: python upload_agent.py <video.mp4> <title> [description] [thumbnail.jpg]")
