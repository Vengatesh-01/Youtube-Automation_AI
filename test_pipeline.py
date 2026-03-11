from topic_agent import generate_topics
from script_agent import generate_script
from voice_agent import generate_voice
from video_agent import create_video
from thumbnail_agent import generate_thumbnail
from upload_agent import upload_video

def test_full_pipeline():
    # Step 1: Fetch topic
    topics = generate_topics()
    topic = topics[0]  # take the first topic for testing
    print(f"Testing with topic: {topic['title']}")

    # Step 2: Generate script
    script = generate_script(topic)
    print("Script generated.")

    # Step 3: Generate voiceover
    voice_file = generate_voice(script)
    print(f"Voiceover created: {voice_file}")

    # Step 4: Create video
    video_file = create_video(script, voice_file)
    print(f"Video created: {video_file}")

    # Step 5: Create thumbnail
    thumbnail_file = generate_thumbnail(topic['title'])
    print(f"Thumbnail created: {thumbnail_file}")

    # Step 6: Upload video
    video_url = upload_video(video_file, topic['title'], topic['description'], thumbnail_file)
    print(f"Uploaded successfully! Video URL: {video_url}")

# Run the test
if __name__ == "__main__":
    test_full_pipeline()
