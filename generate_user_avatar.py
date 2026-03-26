import sys
import os
import argparse

# Add the current directory to sys.path so we can import sadtalker_pipeline
sys.path.append(os.getcwd())

from sadtalker_pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Generate High-Quality AI Avatar Video")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the viral script")
    parser.add_argument("--audio", type=str, help="Path to existing audio file (optional)")
    parser.add_argument("--image", type=str, help="Path to existing image file (optional)")
    parser.add_argument("--script", type=str, help="Path to existing script file (optional)")
    
    args = parser.parse_args()
    
    with open("debug_flow.log", "a") as f: f.write(f"\n--- NEW RUN FOR TOPIC: {args.topic} ---\n")
    
    print(f"Starting High-Quality Generation for Topic: {args.topic}")
    with open("debug_flow.log", "a") as f: f.write("Starting run_pipeline...\n")
    
    success = run_pipeline(
        topic=args.topic,
        audio_path=args.audio,
        image_path=args.image,
        script_path=args.script
    )
    with open("debug_flow.log", "a") as f: f.write(f"run_pipeline finished with success={success}\n")
    
    if success:
        print(" Generation completed successfully!")
        print("Check the 'results/' directory for the final video and 'outputs/' for the portrait image.")
    else:
        print(" Generation failed. Please check the logs above.")

if __name__ == "__main__":
    # Example usage: python generate_user_avatar.py --topic "Mastering the art of focus"
    main()
