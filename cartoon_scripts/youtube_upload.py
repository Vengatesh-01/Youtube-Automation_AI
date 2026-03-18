import os
import requests
import json
import time

# YouTube API setup
# Note: Requires google-api-python-client, google-auth-oauthlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

def get_authenticated_service(config_path):
    if not os.path.exists(config_path):
        print(f"❌ YouTube Config not found: {config_path}")
        return None
    
    # Placeholder for OAuth2 flow
    # In a real scenario, this would load credentials from a token file or run the flow
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    try:
        flow = InstalledAppFlow.from_client_secrets_file(config_path, SCOPES)
        credentials = flow.run_local_server(port=0)
        return build("youtube", "v3", credentials=credentials)
    except Exception as e:
        print(f"❌ YouTube Auth Failed: {e}")
        return None

def upload_video(video_path, title, description, tags, category_id="22", privacy_status="public"):
    print(f"🚀 Uploading {video_path} to YouTube...")
    
    config_path = "youtube_config.json"
    youtube = get_authenticated_service(config_path)
    if not youtube:
        return None

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"✅ Upload successful! Video ID: {response['id']}")
    return response['id']

if __name__ == "__main__":
    # Test call (would fail without config)
    # upload_video("outputs/final_video.mp4", "Test Video", "This is a test", ["test"])
    pass
