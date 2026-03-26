import sys
import os

# Add the current directory to sys.path so we can import sadtalker_pipeline
sys.path.append(os.getcwd())

from sadtalker_pipeline import get_background_prompt

def test_background_selection():
    test_cases = [
        ("coding tips for python", "In this video we will learn how to write clean code..."),
        ("office productivity hacks", "How to manage your time better at the office..."),
        ("morning coffee routine", "Start your day with a perfect espresso..."),
        ("futuristic cyberpunk city", "The year is 2077 and the neon lights are bright...")
    ]
    
    with open("test_results.log", "w") as f:
        for topic, script in test_cases:
            try:
                category = get_background_prompt(topic, script)
                result = f"Topic: {topic} => Selected Background: {category}\n"
            except Exception as e:
                result = f"Topic: {topic} => Error: {e}\n"
            print(result.strip())
            f.write(result)

if __name__ == "__main__":
    test_background_selection()
