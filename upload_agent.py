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

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"


def _get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired YouTube credentials...")
            creds.refresh(Request())
        else:
            # Check for headless environment (e.g., Render)
            is_headless = os.environ.get("RENDER") == "true" or os.environ.get("HEADLESS") == "true"
            
            if is_headless:
                print("❌ ERROR: YouTube token.json is missing or invalid in a headless environment.")
                print("Manual action required: Run this script locally to generate token.json, then upload/commit it.")
                raise Exception("Missing valid YouTube token.json in headless environment.")

            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"{CLIENT_SECRETS_FILE} not found. See setup instructions at the top of upload_agent.py."
                )
            
            print("Starting OAuth flow (Local Server mode)...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=8080, 
                success_message='Authentication successful! You can safely close this browser tab and return to the terminal.'
            )
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_file: str,
    title: str,
    description: str = "",
    thumbnail_file: str = None,
    category_id: str = "22",
    tags=None,
    privacy: str = "public",
) -> str:
    """
    Upload video_file to YouTube.
    Optionally set a thumbnail via thumbnail_file path.
    Returns the YouTube video URL.
    """
    if tags is None:
        tags = ["automation", "trending"]

    print("Authenticating with YouTube API...")
    youtube = _get_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy},
    }

    print(f"Uploading {video_file} ...")
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]

    # Set thumbnail if provided
    if thumbnail_file and os.path.isfile(thumbnail_file):
        print(f"Setting thumbnail: {thumbnail_file}")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_file)
            ).execute()
        except Exception as e:
            print(f"  Warning: Thumbnail upload failed: {e}")
            print("  Video upload was successful, but the thumbnail could not be set (possibly due to account verification).")

    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Uploaded successfully: {url}")
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
