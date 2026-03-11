"""
run_pipeline_now.py — YouTube Automation Immediate Trigger

Runs the full pipeline ONCE, right now, with high-quality settings.
"""

from datetime import datetime
from topic_agent import generate_topics
from script_agent import generate_script
from voice_agent import generate_voice
from video_agent import create_video
from thumbnail_agent import generate_thumbnail
from upload_agent import upload_video

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_now():
    log("🚀 EXECUTING FULL PIPELINE NOW...")

    # Step 1: Topic
    log("Step 1/6 — Generating high-quality niche topic...")
    topics = generate_topics(5)
    # Pick a random one for variety across niches
    import random
    topic = random.choice(topics)
    log(f"Topic Selected: {topic['title']} (Niche: {topic['category']})")

    # Step 2: Script
    log("Step 2/6 — Generating 2-3 minute structured script...")
    script_file = generate_script(topic)

    # Step 3: Voiceover
    log("Step 3/6 — Converting script to professional voiceover...")
    voice_file = generate_voice(script_file)

    # Step 4: Thumbnail
    log("Step 4/6 — Creating bright, clickable thumbnail...")
    thumbnail_file = generate_thumbnail(topic["title"], topic.get("category", "Trending"))

    # Step 5: Video
    log("Step 5/6 — Rendering final MP4 with subtitles...")
    video_file = create_video(script_file, voice_file, topic["title"])

    # Step 6: Upload
    log("Step 6/6 — Uploading to channel...")
    try:
        url = upload_video(video_file, f"{topic['title']} #Shorts", topic.get("description", ""), thumbnail_file)
        log(f"✅ SUCCESS! Video URL: {url}")
        return url
    except Exception as e:
        log(f"❌ Upload failed: {e}")
        log("The rest of the pipeline succeeded. Video is ready in the 'videos/' folder.")
        return None

if __name__ == "__main__":
    run_now()
