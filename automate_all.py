import os
import time
import random

# Set environment variables for automation
os.environ["AUTO_SYNC_TO_CLOUD"] = "true"

def run_daily_automation():
    print("🤖 [ROBOT] Starting Daily YouTube Automation Factory...")
    
    # 1. Choose a motivational topic
    topics = [
        "The Law of Attraction",
        "Overcoming Procrastination",
        "The Power of Habits",
        "Growth Mindset secrets",
        "Financial Freedom principles",
        "The Art of Focus",
        "Building Unstoppable Confidence"
    ]
    selected_topic = random.choice(topics)
    
    print(f"💡 [TOPIC] Selected Topic: {selected_topic}")
    
    # 2. Generate Script (This calls Ollama + Auto-Syncs to GitHub)
    print("✍️ [SCRIPT] Generating Llama3 script and syncing to Cloud...")
    from script_agent import generate_script
    topic_dict = {"title": selected_topic}
    try:
        script_file = generate_script(topic_dict)
        print(f"✅ [SCRIPT] Done! Script saved and pushed to Cloud.")
    except Exception as e:
        print(f"❌ [ERROR] Script generation failed: {e}")
        return

    # 3. Optional: Trigger local production too (if you want the video made here)
    # If you only want Render to make it, we stop here. 
    # If you want your PC to help, uncomment the next line:
    # os.system("python run_pipeline_now.py")

    print("\n🏁 [FACTORY] Shift complete. Every piece is in place.")
    print("If you have Render active, it will now see the new script on GitHub and start building!")

if __name__ == "__main__":
    run_daily_automation()
