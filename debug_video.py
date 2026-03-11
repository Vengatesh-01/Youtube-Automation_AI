from video_agent import create_video
import os

# Create dummy script and voiceover
os.makedirs('temp_test', exist_ok=True)
script_path = 'temp_test/test_script.txt'
with open(script_path, 'w') as f:
    f.write("This is a test script for the upgraded video agent. We are extracting keywords and testing motion graphics.")

# We already have some voiceovers in voiceovers/ folder hopefully
import glob
voiceovers = glob.glob('voiceovers/*.mp3')
if voiceovers:
    try:
        create_video(script_path, voiceovers[0], "Test Video Debug")
    except Exception as e:
        print(f"DEBUG_ERROR: {e}")
else:
    print("No voiceovers found to test.")
