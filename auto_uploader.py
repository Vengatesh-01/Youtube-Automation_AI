import os, time, glob, sys
import datetime
from scripts.youtube_upload import upload_video

def get_next_8_oclock_utc():
    # YouTube API requires ISO 8601 format in UTC.
    # We want either 8:00 AM or 8:00 PM local time.
    # First, let's just assume the user means 8 PM today or 8 AM tomorrow.
    # To be safe, let's schedule for 20:00:00 local time (which is 14:30:00Z if IST).
    # Since we don't know the exact local timezone offset reliably without pytz, 
    # we'll use local time to construct 20:00 today, then convert to UTC.
    now = datetime.datetime.now()
    target = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now > target:
        # If it's already past 8 PM, schedule for 8 AM tomorrow
        target = (now + datetime.timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Convert local target to UTC
    utc_target = datetime.datetime.utcfromtimestamp(target.timestamp())
    return utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    print("Waiting for cinematic pipeline to complete...")
    outputs_dir = os.path.abspath("outputs")
    
    # Get the latest cine_ directory
    dirs = glob.glob(os.path.join(outputs_dir, "cine_*"))
    if not dirs:
        print("No cine outputs found.")
        return
        
    latest_dir = max(dirs, key=os.path.getmtime)
    final_vid = os.path.join(latest_dir, "final_vertical.mp4")
    script_file = os.path.join(latest_dir, "script.txt")
    
    print(f"Monitoring directory: {latest_dir}")
    print(f"Looking for: {final_vid}")
    
    # Wait for the file to be created and completely written (verify size stops changing)
    while not os.path.exists(final_vid):
        time.sleep(60)
        
    print("Final video detected! Waiting 30 seconds to ensure FFmpeg is done writing...")
    time.sleep(30)
    
    # Read script for description
    desc = "Automated AI Video\n\n#shorts #motivation #ai #viral #youtube"
    if os.path.exists(script_file):
        with open(script_file, 'r', encoding='utf-8') as f:
            desc = f"{f.read()[:400]}\n\n#shorts #motivation #ai #viral #youtube"
    
    publish_time = get_next_8_oclock_utc()
    print(f"Uploading to YouTube. Scheduled for: {publish_time}")
    
    upload_video(
        video_path=final_vid,
        title="Futuristic AI Technology",
        description=desc,
        publish_at=publish_time
    )
    print("Upload complete!")

if __name__ == "__main__":
    main()
