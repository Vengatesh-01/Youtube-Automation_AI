import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from script_agent import generate_script

def test_ollama():
    topic = {
        "title": "Discipline",
        "description": "The art of staying consistent even when you don't feel like it.",
        "category": "Motivational"
    }
    
    print("Testing Ollama Script Generation...")
    try:
        script_file = generate_script(topic)
        print(f"✅ Script generated: {script_file}")
        
        with open(script_file, "r", encoding="utf-8") as f:
            content = f.read()
            print("\n--- GENERATED SCRIPT ---")
            print(content)
            print("------------------------")
            
            word_count = len(content.split())
            print(f"Word count: {word_count}")
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_ollama()
